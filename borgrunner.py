#! /usr/bin/env python3

import sys
import config
import subprocess
import argparse

class BackupType:
    BACKUP    = 1
    PRUNE     = 2
    CHECK     = 3
    CHECKFULL = 4
    MOUNT     = 5
    BREAKLOCK = 6
    INFO      = 7


class Borgrunner():

    def __init__( self, a_config ):
        self.config = a_config
        self.create = 'create {flags}  {url}::{prefixName}-{postfixName} {includes} {excludes} {excludefrom}'
        self.prune  = 'prune {prefixFlag} {prunePrefixName} {flags} {keep} {url}'
        self.info = 'info --sort-by name {url}'



        self.flags       = a_config.flags
        self.url         = a_config.url
        self.prefixName  = None
        self.postfixName = None
        self.includes    = None
        self.excludes    = None
        self.excludeFile = None


    def createCommand( self, archive ):
        prefixName  = self.config.getArchiveValue( archive, self.config.prefixName() )
        postfixName = self.config.getArchiveValue( archive, self.config.postfixName() )
        includes    = ' '.join( self.config.getArchiveValue( archive, self.config.includes() ) )
        excludes    = '-e ' + ' -e '.join( self.config.getArchiveValue( archive, self.config.excludes() ) )
        excludeFile = '--exclude-from ' + ' --exclude-from '.join( self.config.getArchiveValue( archive, self.config.exclude_files() ) )
        dryrun      = self.config.dryrun

        flags = self.flags

        if dryrun:
            if '-s' in flags:
                flags.remove( '-s' )
            if '--stats' in flags:
                self.flags.remove( '--stats' )
            flags += [ '--dry-run' ]

        return ( 'borg',
                 self.create.format( flags      =' '.join(flags),
                                     url        =self.url,
                                     prefixName =prefixName,
                                     postfixName=postfixName,
                                     includes   =includes,
                                     excludes   =excludes,
                                     excludefrom=excludeFile )
                 )

    def pruneCommand( self, archive ):
        bUsePrefix  = self.config.getPruneValue( archive, self.config.pruneUsePrefix() )
        dryrun      = self.config.dryrun

        prefixName  = self.config.getArchiveValue( archive, self.config.prefixName() )
        keep        = self.config.getPruneValue( archive, self.config.keep() )

        strKeep = ''
        for key in keep:
            strKeep += "--{}={} ".format( key, keep[ key ] )


        flags = self.config.getPruneValue( archive, self.config.archflags() )

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

        return ( 'borg',
                 self.prune.format( prefixFlag= prefixFlag,
                                    prunePrefixName= prunePrefixName,
                                    flags     = ' '.join( flags ),
                                    keep      = strKeep,
                                    url       = self.url )
                 )

    def infoCommand( self, archive ):
        return ( 'borg', self.info.format( url = self.url ) )


    def show( self ):
        archive = self.config.firstArchive()

        while archive is not None:
            print( "{}".format( self.createCommand( archive )[2] ) )
            print()
            archive = self.config.nextArchive()

    def run( self, a_bVerbose, a_Command: BackupType ):
        archive = self.config.firstArchive()

        while archive is not None:
            if a_Command == BackupType.BACKUP:
                strCmd, strParam = self.createCommand( archive )
            elif a_Command == BackupType.PRUNE:
                strCmd, strParam = self.pruneCommand( archive )
            elif a_Command == BackupType.INFO:
                strCmd, strParam = self.infoCommand( archive )
            else:
                print( 'unknown command' )
                return

            if a_bVerbose == True:
                print( 'exec:{} {}'.format( strCmd, strParam ) )
            strReturn = self.sysCall( strCmd, strParam )
            if a_bVerbose == True:
                print( 'return info: {}'.format( strReturn ) )
            archive = self.config.nextArchive()


    def sysCall( self, a_cmd: str, a_params: str ):
        aCall = []
        aCall.append( a_cmd )
        aCall += a_params.split()

        res = subprocess.run( aCall, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, universal_newlines=True )
        if res.returncode == 0:
            return 'completed: {}'.format( res.stdout )
        else:
            return 'failed: {}'.format( res.stderr )



def usage( a_args ):
    print( 'usage: {} yaml.yaml command,...'.format( a_args[0] ) )
    print( '  commands: backup, prune, info, list, check fullcheck, mount, umount, break-lock' )


def main( a_argv=None ):
    if a_argv is None:
        a_argv = sys.argv

    if len( a_argv ) < 2:
        usage( a_argv )
        sys.exit( 1 )

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

    parser.add_argument( '-P' '--pass', type=str, help='borg passphase' )
    parser.add_argument( '-v', '--verbose', help='borg passphase', action='store_true' )
    parser.add_argument( '--version',      help='borg passphase' )

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




    conf = config.Config()
    conf.open( "test.yaml" )
    #config.print()

    borg = Borgrunner( conf )

    for strCommand in a_argv[2:]:
        if strCommand == 'backup':
            borg.run( pargs.verbose, BackupType.BACKUP )
        elif strCommand == 'prune':
            borg.run( pargs.verbose, BackupType.PRUNE )
        elif strCommand == 'info':
            borg.run( pargs.verbose, BackupType.INFO )
        else:
            print( 'Unknown command: {}'.format( strCommand ) )
            sys.exit( 1 )

    print( 'completed' )

if __name__ == "__main__":
    sys.exit( main( sys.argv ) )
