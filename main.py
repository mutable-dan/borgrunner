#! /usr/bin/env python3

import sys
import yaml
import subprocess

class BackupType:
    BACKUP    = 1
    PRUNE     = 2
    CHECK     = 3
    CHECKFULL = 4
    MOUNT     = 5
    BREAKLOCK = 6



class Config():

    def __init__( self ):
        self.url = ''

    def open( self, a_strConfigPath ):
        with open( a_strConfigPath, 'r' ) as stream:
            try:
                yml = yaml.safe_load( stream )
                self.url   = yml['repos']['url']
                self.flags = yml['repos']['flags']

                #len( yml['repos'] )
                self.archive = yml[ 'repos' ][ 'archive' ]
                self.archiveIndex = 0

            except yaml.YAMLError as e:
                print( 'Error in config file' )


    def archiveCount( self ):
        return len( self.archive )

    def firstArchive( self ):
        self.archiveIndex = 0
        return self.archive[ self.archiveIndex ]

    def nextArchive( self ):
        if self.archiveIndex < self.archiveCount():
            self.archiveIndex += 1
            if self.archiveIndex >= self.archiveCount():
                return None
            else:
                return self.archive[ self.archiveIndex ]

    def getArchive( self ):
        return self.archive[ self.archiveIndex ]

    def getArchiveValue( self, archive, name ):
        return archive[ name ]

    def getPrune( self, archive ):
        return archive[ 'prune' ]

    def getPruneValue( self, archive, name ):
        return archive[ 'prune' ][ name ]

    @property
    def url( self ):
            return self.__url
    @url.setter
    def url( self, value ):
            self.__url = value

    @property
    def flags( self ):
            return self.__flags
    @flags.setter
    def flags( self, value ):
        self.__flags = value


    @property
    def archive( self ):
            return self.__archive
    @archive.setter
    def archive( self, value ):
            self.__archive = value

    def prefixName( self ):
        return 'prefixName'

    def postfixName( self ):
        return 'postfixName'

    def dryrun( self ):
        return 'dryrun'

    def includes( self ):
        return 'includes'

    def excludes( self ):
        return 'excludes'

    def exclude_files( self ):
        return 'exclude-files'

    def pruneUsePrefix( self ):
        return 'usePrefix'

    def archflags( self ):
        return 'flags'

    def keep( self ):
        return 'keep'

    def print( self ):
        print( "config:" )
        print( "  url           :", self.url )
        print( "  flags         :", self.flags )
        print()

        for item in self.archive:
            print( "  prefixName    :", self.getArchiveValue( item, self.prefixName()    ) )
            print( "  postfixName   :", self.getArchiveValue( item, self.postfixName()   ) )
            print( "  flags         :", self.getArchiveValue( item, self.archflags()     ) )
            print( "  dry-run       :", self.getArchiveValue( item, self.dryrun()        ) )
            print( "  includes      :", self.getArchiveValue( item, self.includes()      ) )
            print( "  excludes      :", self.getArchiveValue( item, self.excludes()      ) )
            print( "  exclude-files :", self.getArchiveValue( item, self.exclude_files() ) )
            print( "    prune prefix:", self.getPruneValue  ( item, self.pruneUsePrefix()) )
            print( "     keep       :", self.getPruneValue  ( item, self.keep()          ) )
            print( '  -----------------------------------------------------' )



class Borgrunner():

    def __init__( self, a_config ):
        self.config = a_config
        self.create = 'create {flags}  {url}::{prefixName}-{postfixName} {includes} {excludes} {excludefrom}'
        self.prune  = 'prune {prefixFlag} {prefixName} {flags} {keep} {url}'


        self.flags       = a_config.flags
        self.url         = a_config.url
        self.prefixName  = None
        self.postfixName = None
        self.includes    = None
        self.excludes    = None
        self.excludeFile = None
        self.dryrun      = False

    def createCommand( self, archive ):
        prefixName  = self.config.getArchiveValue( archive, self.config.prefixName() )
        postfixName = self.config.getArchiveValue( archive, self.config.postfixName() )
        includes    = ' '.join( self.config.getArchiveValue( archive, self.config.includes() ) )
        excludes    = '-e ' + ' -e '.join( self.config.getArchiveValue( archive, self.config.excludes() ) )
        excludeFile = '--exclude-from ' + ' --exclude-from '.join( self.config.getArchiveValue( archive, self.config.exclude_files() ) )
        dryrun      = self.config.getArchiveValue( archive, self.config.dryrun() )

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
        dryrun      = self.config.getPruneValue( archive, self.config.dryrun() )

        prefixName  = self.config.getArchiveValue( archive, self.config.prefixName() )
        keep        = self.config.getPruneValue( archive, self.config.keep() )

        flags = self.config.getPruneValue( archive, self.config.archflags() )

        if dryrun:
            if '-s' in flags:
                flags.remove( '-s' )
            if '--stats' in flags:
                flags.remove( '--stats' )
            flags += [ '--dry-run' ]

        prefixFlag = '-P'
        if bUsePrefix == False:
            prefixFlag = ''
            prefixName = ''

        return ( 'borg',
                 self.prune.format( prefixFlag= prefixFlag,
                                    prefixName= prefixName,
                                    flags     = ' '.join( flags ),
                                    keep      = ' '.join( keep ),
                                    url       = self.url )
                 )


    def show( self ):
        archive = self.config.firstArchive()

        while archive is not None:
            print( "{}".format( self.createCommand( archive )[2] ) )
            print()
            archive = self.config.nextArchive()

    def run( self, a_Command: BackupType ):
        archive = self.config.firstArchive()

        while archive is not None:
            if a_Command == BackupType.BACKUP:
                strCmd, strParam = self.createCommand( archive )
            elif a_Command == BackupType.PRUNE:
                strCmd, strParam = self.pruneCommand( archive )
            else:
                print( 'unknow command' )
                return

            print( 'exec:{} {}'.format( strCmd, strParam ))
            self.sysCall( strCmd, strParam )
            archive = self.config.nextArchive()


    def sysCall( self, a_cmd: str, a_params: str ):
        aCall = []
        aCall.append( a_cmd )
        aCall += a_params.split()

        res = subprocess.run( aCall, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, universal_newlines=True )
        if res.returncode == 0:
            print( 'ok', res.stdout )
        else:
            print( '!ok', res.stderr )
        print( 'done' )



def sysCall( a_cmd: str, a_params: str ):
    lstParam = a_params.split()
    aCall = [ str(a_cmd) ] + lstParam


    res = subprocess.run( aCall, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, universal_newlines=True )
    if res.returncode == 0:
        print( 'ok', res.stdout )
    else:
        print( '!ok', res.stderr )
    print( 'done' )


def main( a_argv=None ):
    if a_argv is None:
        a_argv = sys.argv

    sysCall( 'find', '. -name main.py' )

    config = Config()
    config.open( "test.yaml" )
    config.print()

    borg = Borgrunner( config )
    borg.run( BackupType.BACKUP )
    print( ' prune -------' )
    borg.run( BackupType.PRUNE )



if __name__ == "__main__":
    sys.exit( main( sys.argv ) )
