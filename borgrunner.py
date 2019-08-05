#! /usr/bin/env python3

import sys
import config
import subprocess
import argparse
import logging

g_loggerName = 'borg'

class BackupType:
    BACKUP    = 1
    PRUNE     = 2
    CHECK     = 3
    CHECKFULL = 4
    MOUNT     = 5
    BREAKLOCK = 6
    INFO      = 7
    LIST      = 8


class Borgrunner():

    def __init__( self, config, logname ):
        self.command = 'borg'
        self.config = config
        self.log = logging.getLogger( logname )


        # self.flags       = config.flags
        self.url         = config.url
        self.prefixName  = None
        self.postfixName = None
        # self.includes    = None
        # self.excludes    = None
        # self.excludeFile = None
        self.password    = None
        self.rsh         = None


    def passwd( self, a_strPwd: str ):
        self.password = a_strPwd

    def privateKey( self, a_strPathToKey ):
        self.rsh = 'ssh -i ' + a_strPathToKey

    '''
    borg command to amke a backup snapshot
    '''
    def createCommand( self, archive ):
        strcreatecmd = 'create {flags} {url}::{prefixName}-{postfixName} {includes} {excludes} {excludefrom}'

        prefixName  = self.config.getArchiveValue( archive, self.config.prefixName() )
        postfixName = self.config.getArchiveValue( archive, self.config.postfixName() )

        includes    = str()
        excludes    = str()
        excludeFile = str()

        lstInclude = self.config.getBackupValue( archive, self.config.backup_includes() )
        if lstInclude is not None:
            includes    = ' '.join( lstInclude )
        else:
            includes = ''

        lstExcludes = self.config.getBackupValue( archive, self.config.backup_excludes() )
        if lstExcludes is not None:
            excludes = '-e ' + ' -e '.join( lstExcludes )
        else:
            excludes = ''

        lstExclFrom = self.config.getBackupValue( archive, self.config.backup_exclude_files() )
        if lstExclFrom is not None:
            excludeFile = '--exclude-from ' + ' --exclude-from '.join( lstExclFrom )
        else:
            excludeFile = ''

        dryrun      = self.config.dryrun
        flags = self.config.getBackupValue( archive, self.config.backup_flags() )

        if self.url is None: return False, None
        postfixName = postfixName if not None else ''
        dryrun      = dryrun      if not None else False
        flags       = flags       if not None else []

        if dryrun:
            if '-s' in flags:
                flags.remove( '-s' )
            if '--stats' in flags:
                self.flags.remove( '--stats' )
            flags += [ '--dry-run' ]

        return strcreatecmd.format( flags      =' '.join(flags),
                                     url        =self.url,
                                     prefixName =prefixName,
                                     postfixName=postfixName,
                                     includes   =includes,
                                     excludes   =excludes,
                                     excludefrom=excludeFile )

    '''
    borg command for pruning snapshots
    '''
    def pruneCommand( self, archive ):
        prune  = 'prune {prefixFlag} {prunePrefixName} {flags} {keep} {url}'

        bUsePrefix  = self.config.getPruneValue( archive, self.config.pruneUsePrefix() )
        dryrun      = self.config.dryrun

        prefixName  = self.config.getArchiveValue( archive, self.config.prefixName() )
        keep        = self.config.getPruneValue( archive, self.config.prune_keep() )

        if prefixName is None:
            # error condition
            return False, None

        flags = self.config.getPruneValue( archive, self.config.prune_flags() )

        if self.url is None: return False, None
        bUsePrefix  = bUsePrefix  if not None else False
        dryrun      = dryrun      if not None else False
        flags       = flags       if not None else []
        keep        = keep        if not None else []

        strKeep = ''
        for key in keep:
            strKeep += "--{}={} ".format( key, keep[ key ] )

        if dryrun:
            if '-s' in flags:
                flags.remove( '-s' )
            if '--stats' in flags:
                flags.remove( '--stats' )
            flags += [ '--dry-run' ]

        prunePrefixName = prefixName
        prefixFlag = '-P'
        if bUsePrefix == False:
            prefixFlag      = ''
            prunePrefixName = ''

        return  prune.format( prefixFlag= prefixFlag,
                                    prunePrefixName= prunePrefixName,
                                    flags     = ' '.join( flags ),
                                    keep      = strKeep,
                                    url       = self.url )

    '''
    borg in fo command
    '''
    def infoCommand( self ):
        info = 'info --sort-by name {url}'
        return  info.format( url = self.url )

    '''
    broken borg list
        parsing for sys call is broken
    '''
    def listCommand( self ):
        strlist = 'list --sort-by name --format="{{time}} --> {{name}}{{LF}}" {url}'.format( url= self.url )
        return strlist



    '''
    run a borg command
    '''
    def run( self, command: BackupType ):
        bRes, archive = self.config.firstArchive()
        if bRes == False:
            return

        # cooomands that work on repo
        # info
        # list
        if command == BackupType.INFO:
            strParam = self.infoCommand()
        elif command == BackupType.LIST:
            strParam = self.listCommand( )
        else:
            while archive is not None:
                strCurrentCommand = 'na'
                if command == BackupType.BACKUP:
                    strParam = self.createCommand( archive )
                    strCurrentCommand = 'backup/create'
                elif command == BackupType.PRUNE:
                    strParam = self.pruneCommand( archive )
                    strCurrentCommand = 'prune'
                else:
                    self.log.warning( 'unknown command:{}'.format( command ) )
                    return

                self.log.debug( 'exec:{} {}'.format( self.command, strParam ) )
                self.log.info( '{} archive:{}'.format( strCurrentCommand, self.config.getArchiveValue( archive, self.config.prefixName() ) ) )

                bSuceeded, strReturn = self.sysCall( self.command, strParam )
                for str in strReturn.split( '\n' ):
                    if bSuceeded == True:
                        self.log.info( '{}'.format( str ) )
                    else:
                        self.log.error( '{}'.format( str ) )

                bRes, archive = self.config.nextArchive()
            return

        self.log.debug( 'exec:{} {}'.format( self.command, strParam ) )

        bSuceeded, strReturn = self.sysCall( self.command, strParam )
        for str in strReturn.split( '\n' ):
            if bSuceeded == True:
                self.log.info( '{}'.format( str ) )
            else:
                self.log.error( '{}'.format( str ) )


    '''
    do the system call
    '''
    def sysCall( self, a_cmd: str, params: str ):

        denv = {}
        if self.password is not None:
            denv = { 'BORG_PASSPHRASE' : self.password }
            self.log.debug( 'setting BORG_PASSPHRASE {}'.format( self.password ) )
        if self.rsh is not None:
            denv[ 'BORG_RSH' ] = self.rsh
            self.log.debug( 'setting BORG_RSH {}'.format( self.rsh ) )

        strc = a_cmd + ' ' + params
        try:
            if len( denv ) > 0:
                res = subprocess.run( strc, shell=True, env=denv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, universal_newlines=True )
            else:
                res = subprocess.run( strc, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, universal_newlines=True )

            if res.returncode == 0:
                if len( res.stdout ) > 0:
                    return True, '{}'.format( res.stdout )
                else:
                    return True, '{}'.format( res.stderr )
            else:
                return False, '{}'.format( res.stderr )
        except FileNotFoundError as fnfe:
            return False, fnfe.strerror
        except subprocess.CalledProcessError as cpe:
            self.log.error( cpe.output )
            return False, cpe.output
        except:
            return False, 'error calling borg: {}'.format( strc )



def usage( a_args ):
    print( 'usage: {} yaml.yaml command,...'.format( a_args[0] ) )
    print( '  commands: backup, prune, info, list, check fullcheck, mount, umount, break-lock' )

def exitFailed():
    sys.exit( 1 )

def exitOK():
    sys.exit( 0 )

def main( a_argv=None ):
    if a_argv is None:
        a_argv = sys.argv

    if len( a_argv ) < 2:
        usage( a_argv )
        exitFailed()

    strAllcommands = 'backup, prune, info, list check fullcheck, mount, umount, break-lock'
    parser = argparse.ArgumentParser( 'borgrunner' )
    parser.add_argument( 'yaml_arg', type=str, help='Path to yaml config file' )
    parser.add_argument( 'command_arg0', type=str, help='Backup command: ' + strAllcommands )
    parser.add_argument( 'command_arg1', type=str, help='Backup command: ' + strAllcommands, nargs='?' )
    parser.add_argument( 'command_arg2', type=str, help='Backup command: ' + strAllcommands, nargs='?' )
    parser.add_argument( 'command_arg3', type=str, help='Backup command: ' + strAllcommands, nargs='?' )
    parser.add_argument( 'command_arg4', type=str, help='Backup command: ' + strAllcommands, nargs='?' )
    parser.add_argument( 'command_arg5', type=str, help='Backup command: ' + strAllcommands, nargs='?' )
    parser.add_argument( 'command_arg6', type=str, help='Backup command: ' + strAllcommands, nargs='?' )
    parser.add_argument( 'command_arg7', type=str, help='Backup command: ' + strAllcommands, nargs='?' )
    parser.add_argument( 'command_arg8', type=str, help='Backup command: ' + strAllcommands, nargs='?' )

    parser.add_argument( '-P', '--password', type=str, help='borg passphase' )
    parser.add_argument( '-i',               type=str, help='borg path to ssh key' )
    parser.add_argument( '-v', '--verbose',            help='verbose mode', action='store_true' )
    parser.add_argument( '--version',                  help='borg version' )
    parser.add_argument( '-l', '--logpath', type=str, help='log path' )

    pargs = parser.parse_args()

    strLogPath = pargs.logpath
    if strLogPath is None:
        strLogPath = 'borgrunner.log'

    log = logging.getLogger( g_loggerName )
    log.setLevel( logging.INFO )
    logFileHandler = logging.FileHandler( strLogPath )
    logConsoleHandler = logging.StreamHandler()
    logFormatter = logging.Formatter( '%(asctime)s - %(name)s - %(levelname)s - %(message)s' )
    consoleFormatter = logging.Formatter( '%(levelname)s - %(message)s' )

    logFileHandler.setFormatter( logFormatter )
    logConsoleHandler.setFormatter( consoleFormatter )
    log.addHandler( logFileHandler )
    log.addHandler( logConsoleHandler )




    if pargs.verbose == True:
        log.info( 'debug logging' )
        log.setLevel( logging.DEBUG )
        logFileHandler.setLevel( logging.DEBUG )
        logConsoleHandler.setLevel( logging.DEBUG )
    else:
        log.setLevel( logging.INFO )
        logFileHandler.setLevel( logging.INFO )
        logConsoleHandler.setLevel( logging.INFO )

    log.info( '{} starting'.format( a_argv[0] ) )

    strMsg1 = 'config: {}'.format( pargs.yaml_arg )
    strMsg2 = 'commands: {}, {}, {}, {}, {}, {}, {}, {}'.format(
        pargs.command_arg0, pargs.command_arg1,
        pargs.command_arg2, pargs.command_arg3,
        pargs.command_arg3, pargs.command_arg5,
        pargs.command_arg6, pargs.command_arg7,
        pargs.command_arg8 )
    log.debug( strMsg1 )
    log.debug( strMsg2 )

    lstCommand = []
    lstCommand.append( pargs.command_arg0 )
    if pargs.command_arg1 is not None:
        lstCommand.append( pargs.command_arg1 )
    if pargs.command_arg2 is not None:
        lstCommand.append( pargs.command_arg2 )
    if pargs.command_arg3 is not None:
        lstCommand.append( pargs.command_arg3 )
    if pargs.command_arg4 is not None:
        lstCommand.append( pargs.command_arg4 )
    if pargs.command_arg5 is not None:
        lstCommand.append( pargs.command_arg5 )
    if pargs.command_arg6 is not None:
        lstCommand.append( pargs.command_arg6 )
    if pargs.command_arg7 is not None:
        lstCommand.append( pargs.command_arg7 )
    if pargs.command_arg8 is not None:
        lstCommand.append( pargs.command_arg8 )

    conf = config.Config()
    if conf.open( pargs.yaml_arg ) == False:
        for strError in conf.getErrors():
            log.error( strError )
        exitFailed()

    log.debug( conf.show() )

    borg = Borgrunner( config=conf, logname=g_loggerName )
    if pargs.password is not None:
        borg.passwd( pargs.password )

    if pargs.i is not None:
        borg.privateKey( pargs.i )


    for strCommand in lstCommand:
        log.info( "------------- {} -------------".format( strCommand ) )
        if strCommand == 'backup':
            borg.run( BackupType.BACKUP )
        elif strCommand == 'prune':
            borg.run( BackupType.PRUNE )
        elif strCommand == 'info':
            borg.run( BackupType.INFO )
        elif strCommand == 'list':
            borg.run( BackupType.LIST )
        else:
            log.warning( 'Unknown command: {}'.format( strCommand ) )
            exitFailed()

    log.info( 'completed' )
    logging.shutdown()

if __name__ == "__main__":
    sys.exit( main( sys.argv ) )
