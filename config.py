import yaml

class Config():

    def __init__( self ):
        self.url = ''


    def open( self, a_strConfigPath ):
        with open( a_strConfigPath, 'r' ) as stream:
            try:
                yml = yaml.safe_load( stream )
                self.url   = yml['repos']['url']
                self.flags = yml['repos']['flags']
                self.dryrun= yml['repos']['dry-run']

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

    '''
    def dryrun( self ):
        return 'dryrun'
    '''
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

