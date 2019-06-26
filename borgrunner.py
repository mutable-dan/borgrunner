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

    def __init__( self, a_config ):
        self.command = 'borg'
        self.config = a_config


        self.flags       = a_config.flags
        self.url         = a_config.url
        self.prefixName  = None
        self.postfixName = None
        self.includes    = None
        self.excludes    = None
        self.excludeFile = None
        self.password    = None
        self.rsh         = None


    def passwd( self, a_strPwd: str ):
        self.password = a_strPwd

    def privateKey( self, a_strPathToKey ):
        self.rsh = 'ssh -i ' + a_strPathToKey

    '''
    borg command to amke a backup snapshot
    '''
    def createCommand( self, a_archive ):
        strcreatecmd = 'create {flags} {url}::{prefixName}-{postfixName} {includes} {excludes} {excludefrom}'

        prefixName  = self.config.getArchiveValue( a_archive, self.config.prefixName() )
        postfixName = self.config.getArchiveValue( a_archive, self.config.postfixName() )

        includes    = str()
        excludes    = str()
        excludeFile = str()

        lstInclude = self.config.getArchiveValue( a_archive, self.config.includes() )
        if lstInclude is not None:
            includes    = ' '.join( lstInclude )
        else:
            includes = ''

        lstExcludes = self.config.getArchiveValue( a_archive, self.config.excludes() )
        if lstExcludes is not None:
            excludes = '-e ' + ' -e '.join( lstExcludes )
        else:
            excludes = ''

        lstExclFrom = self.config.getArchiveValue( a_archive, self.config.exclude_files() )
        if lstExclFrom is not None:
            excludeFile = '--exclude-from ' + ' --exclude-from '.join( lstExclFrom )
        else:
            excludeFile = ''



        dryrun      = self.config.dryrun
        flags = self.flags

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
    def pruneCommand( self, a_archive ):
        prune  = 'prune {prefixFlag} {prunePrefixName} {flags} {keep} {url}'

        bUsePrefix  = self.config.getPruneValue( a_archive, self.config.pruneUsePrefix() )
        dryrun      = self.config.dryrun

        prefixName  = self.config.getArchiveValue( a_archive, self.config.prefixName() )
        keep        = self.config.getPruneValue( a_archive, self.config.keep() )

        if prefixName is None:
            # error condition
            return False, None

        flags = self.config.getPruneValue( a_archive, self.config.archflags() )

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
    def show( self ):
        archive = self.config.firstArchive()

        while archive is not None:
            print( "{}".format( self.createCommand( archive )[2] ) )
            print()
            archive = self.config.nextArchive()
    '''

    '''
    run a borg command
    '''
    def run( self, a_bVerbose: bool, a_Command: BackupType ):
        bRes, archive = self.config.firstArchive()
        if bRes == False:
            return

        while archive is not None:
            if a_Command == BackupType.BACKUP:
                strParam = self.createCommand( archive )
            elif a_Command == BackupType.PRUNE:
                strCmd, strParam = self.pruneCommand( archive )
            elif a_Command == BackupType.INFO:
                strParam = self.infoCommand( )
            elif a_Command == BackupType.LIST:
                strParam = self.listCommand( )
            else:
                print( 'unknown command' )
                return

            if a_bVerbose == True:
                print( 'exec:{} {}'.format( self.command, strParam ) )

            strReturn = self.sysCall( self.command, strParam )
            if a_bVerbose == True:
                print( 'return info: {}'.format( strReturn ) )
            bRes, archive = self.config.nextArchive()


    '''
    do the system call
    '''
    def sysCall( self, a_cmd: str, a_params: str ):
        # aCall = []
        # aCall.append( a_cmd )
        # aCall += a_params

        if self.password is not None:
            denv = { 'BORG_PASSPHRASE' : self.password }

        if self.rsh is not None:
            denv[ 'BORG_RSH' ] = self.rsh

            res = subprocess.run( aCall, shell=False, env=denv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
                                  universal_newlines=True )
        else:
            strc = a_cmd + ' ' + a_params
            res = subprocess.run( strc, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, universal_newlines=True )

        if res.returncode == 0:
            return 'completed: {}'.format( res.stdout )
        else:
            return 'failed: {}'.format( res.stderr )



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

    log = logging.getLogger( g_loggerName )
    log.setLevel( logging.INFO )
    logFileHandler = logging.FileHandler( 'borgrunner.log' )
    logConsoleHandler = logging.StreamHandler()
    formatter = logging.Formatter( '%(asctime)s - %(name)s - %(levelname)s - %(message)s' )

    logFileHandler.setLevel( logging.INFO )
    logConsoleHandler.setLevel( logging.INFO )
    logFileHandler.setFormatter( formatter )
    log.addHandler( logFileHandler )
    log.addHandler( logConsoleHandler )

    log.info( '{} starting'.format( a_argv[0] ) )

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

    pargs = parser.parse_args()
    if pargs.verbose == True:
        print( 'config: {}'.format( pargs.yaml_arg ) )
        print( 'commands: {}, {}, {}, {}, {}, {}, {}, {}'.format(
            pargs.command_arg0, pargs.command_arg1,
            pargs.command_arg2, pargs.command_arg3,
            pargs.command_arg3, pargs.command_arg5,
            pargs.command_arg6, pargs.command_arg7,
            pargs.command_arg8   ) )

        print()

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
        print( "error", conf.getErrors() )
        exitFailed()

    if pargs.verbose == True:
        print( conf.yaml() )

    borg = Borgrunner( conf )
    if pargs.password is not None:
        borg.passwd( pargs.password )

    if pargs.i is not None:
        borg.privateKey( pargs.i )


    for strCommand in lstCommand:
        if strCommand == 'backup':
            borg.run( pargs.verbose, BackupType.BACKUP )
        elif strCommand == 'prune':
            borg.run( pargs.verbose, BackupType.PRUNE )
        elif strCommand == 'info':
            borg.run( pargs.verbose, BackupType.INFO )
        elif strCommand == 'list':
            borg.run( pargs.verbose, BackupType.LIST )
        else:
            print( 'Unknown command: {}'.format( strCommand ) )
            exitFailed()

    print( 'completed' )

if __name__ == "__main__":
    sys.exit( main( sys.argv ) )
