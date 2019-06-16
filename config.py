import yaml

'''
    read a ymal file in the form of:
    ---
    repos:
        url: "repo"
        flags: [ -s, --list, --filter, AME ]
        dry-run: false
        
        archive:
          - prefixName:  "test-report-dir1-dir2"
            postfixName: "{now:%Y-%m-%dT%H:%M:%S}"
            flags: [ "--one-file-system" ]
            includes: [ 'test-docs/dir1', 'test-docs/dir2' ]
            excludes: [ "test-docs/dir1/f1", "test-docs/dir2/f2" ]
            exclude-files: [ "test-docs/excludes" ]
            prune:
                usePrefix: true
                dryrun: false
                flags: [ "--stats", "--list", "--save-space" ]
                keep: { "keep-daily"  : 14,
                        "keep-weekly" : 12,
                        "keep-monthly": 12,
                        "keep-yearly" : 2
                      }
    
          - prefixName:  "test-report-dir3"
            postfixName: "{now:%Y-%m-%dT%H:%M:%S}"
            flags: [ "--one-file-system" ]
            includes: [ 'test-docs/dir3' ]
            excludes: [ "test-docs/dir3/f2" ]
            exclude-files: [ "test-docs/excludes" ]
            prune:
                usePrefix: true
                flags: [ "--stats", "--list", "--save-space" ]
                keep: { "keep-daily"  : 7,
                        "keep-weekly" : 24,
                        "keep-monthly": 5,
                        "keep-yearly" : 3
                      }
    ...
    a repo points to a uri of a borg repo
    each repo devices archives that will be backed up
    the archive defines it's name (prefixName) and a postfix name which is usually a timestamp
        ex name-2019-06-16--13:59:00
    each archive will define pruning commands
    
    todo:
        error handing
            no printing
            error handing methods
        allow empty prune
         
'''
class Config():

    def __init__( self ):
        self.url = ''


    def open( self, a_strConfigPath ):
        with open( a_strConfigPath, 'r' ) as stream:
            try:
                yml = yaml.safe_load( stream )
                self.url   = yml['repos']['url']
                self.dryrun= yml['repos']['dryrun']
                self.flags = yml['repos']['flags']

                self.archive = yml[ 'repos' ][ 'archive' ]
                self.archiveIndex = 0

            except yaml.YAMLError as e:
                print( 'Error in config file' )


    def archiveCount( self ):
        return len( self.archive )

    '''
    point to the first archive
    '''
    def firstArchive( self ):
        self.archiveIndex = 0
        return self.archive[ self.archiveIndex ]

    '''
    point to the next archive
    '''
    def nextArchive( self ):
        if self.archiveIndex < self.archiveCount():
            self.archiveIndex += 1
            if self.archiveIndex >= self.archiveCount():
                return None
            else:
                return self.archive[ self.archiveIndex ]

    '''
    return current archive pointed to
    '''
    def getArchive( self ):
        return self.archive[ self.archiveIndex ]

    '''
    get a value in the archive elemenet
    '''
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
    def dryrun( self ):
            return self.__dryrun
    @flags.setter
    def dryrun( self, value ):
        self.__dryrun = value


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
        print( "  dry-run       :", self.dryrun )
        print()

        for item in self.archive:
            print( "  prefixName    :", self.getArchiveValue( item, self.prefixName()    ) )
            print( "  postfixName   :", self.getArchiveValue( item, self.postfixName()   ) )
            print( "  flags         :", self.getArchiveValue( item, self.archflags()     ) )
            print( "  includes      :", self.getArchiveValue( item, self.includes()      ) )
            print( "  excludes      :", self.getArchiveValue( item, self.excludes()      ) )
            print( "  exclude-files :", self.getArchiveValue( item, self.exclude_files() ) )
            print( "    prune prefix:", self.getPruneValue  ( item, self.pruneUsePrefix()) )
            print( "     keep       :", self.getPruneValue  ( item, self.keep()          ) )
            print( '  -----------------------------------------------------' )

