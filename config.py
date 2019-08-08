import yaml

'''
    read a ymal file in the form of:
    ---
    repos:
        url: "repo"
        dry-run: false
        
        archive:
          - prefixName:  "test-report-dir1-dir2"
            postfixName: "{now:%Y-%m-%dT%H:%M:%S}"

            backup:
                flags: [ -s, --list, --filter, AME, --one-file-system  ]
                includes: [ 'test-docs/dir1', 'test-docs/dir2' ]
                excludes: [ "test-docs/dir1/f1", "test-docs/dir2/f2" ]
                exclude-files: [ "test-docs/excludes" ]
                
            info:
              flags [ --sort-by name ]
    
            list:
              flags: [ --sort-by name ]
                
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

            backup:
                flags: [ -s, --list, --filter, AME, --one-file-system  ]
                includes: [ 'test-docs/dir3' ]
                excludes: [ "test-docs/dir3/f2" ]
                exclude-files: [ "test-docs/excludes" ]
                
            info:
              flags [ --sort-by name ]
    
            list:
              flags: [ --sort-by name ]

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
        self.errors = []


    def open( self, a_strConfigPath ):
        with open( a_strConfigPath, 'r' ) as stream:
            try:
                yml = yaml.safe_load( stream )
                if not self.exists( yml, 'repos' ):
                    self.setError( 'no repo key in yaml' )
                    return False
                repo = yml[ 'repos' ]

                self.url   = repo[ 'url' ]  if self.exists( repo, 'url'    ) else None
                self.dryrun= repo['dryrun'] if self.exists( repo, 'dryrun' ) else False
                #self.flags = repo['flags']  if self.exists( repo, 'flags'  ) else None

                if self.exists( repo, 'archive' ):
                    self.archive = repo[ 'archive' ]
                else:
                    self.archive = None
                    self.setError( 'no archive section' )
                    return False

                self.archiveIndex = 0

            except yaml.YAMLError as e:
                self.setError( 'Error in config file: {}'.format( e ) )
                return False
            else:
                return True

    def setError( self, a_strMessage: str ):
        self.errors.append( a_strMessage )

    def isError( self ):
        return len( self.errors ) > 0

    def getErrors( self ):
        return self.errors

    def exists( self, a_obj, a_strValue:str ):
        return a_strValue in a_obj


    def archiveCount( self ):
        return len( self.archive )


    '''
    point to the first archive
    '''
    def firstArchive( self ):
        self.archiveIndex = 0
        if len( self.archive ) > 0 and self.archive is not None:
            return True, self.archive[ self.archiveIndex ]
        else:
            return False, None

    '''
    point to the next archive
    '''
    def nextArchive( self ):
        if self.archiveIndex < self.archiveCount():
            self.archiveIndex += 1
            if self.archiveIndex >= self.archiveCount():
                return False, None
            else:
                return True, self.archive[ self.archiveIndex ]

    '''
    return current archive pointed to
    '''
    def getArchive( self ):
        if self.a_archive is not None:
            return self.archive[ self.archiveIndex ]
        else:
            return None

    '''
    get a value in the archive elemenet
    '''
    def getArchiveValue( self, a_archive, a_strName ):
        if a_archive is not None:
            return a_archive[ a_strName ] if self.exists( a_archive, a_strName ) else None
        else:
            return None

    def getPrune( self, a_archive ):
        if a_archive is not None:
            return a_archive['prune'] if self.exists( a_archive, 'prune' ) else None
        else:
            return None

    def getBackupValue( self, a_archive, a_strName ):
        if a_archive is not None:
            if self.exists( a_archive, 'backup' ):
                return a_archive['backup'][ a_strName ] if self.exists( a_archive['backup'], a_strName ) else None
        return None

    def getInfoValue( self, a_archive, a_strName ):
        if a_archive is not None:
            if self.exists( a_archive, 'backup' ):
                return a_archive['info'][ a_strName ] if self.exists( a_archive['info'], a_strName ) else None
        return None

    def getListValue( self, a_archive, a_strName ):
        if a_archive is not None:
            if self.exists( a_archive, 'list' ):
                return a_archive['list'][ a_strName ] if self.exists( a_archive['list'], a_strName ) else None
        return None


    def getPruneValue( self, a_archive, a_strName ):
        if a_archive is not None:
            if self.exists( a_archive, 'prune' ):
                return a_archive['prune'][ a_strName ] if self.exists( a_archive['prune'], a_strName ) else None
        return None


    '''
    repo related tags
    '''
    @property
    def url( self ):
        return self.__url
    @url.setter
    def url( self, value ):
        self.__url = value

    @property
    def dryrun( self ):
        return self.__dryrun
    @dryrun.setter
    def dryrun( self, value ):
        self.__dryrun = value

    @property
    def archive( self ):
        return self.__archive
    @archive.setter
    def archive( self, value ):
        self.__archive = value

    '''
    archive related tags
    '''
    def prefixName( self ):
        return 'prefixName'

    def postfixName( self ):
        return 'postfixName'

    '''
    backup related tags
    '''
    def backup_flags( self ):
        return 'flags'

    def backup_includes( self ):
        return 'includes'

    def backup_excludes( self ):
        return 'excludes'

    def backup_exclude_files( self ):
        return 'exclude-files'

    '''
    info related tags
    '''
    def info_flags( self ):
        return 'flags'

    '''
    list related tags
    '''
    def list_flags( self ):
        return 'flags'


    '''
    prune related tags
    '''
    def prune_usePrefix( self ):
        return 'usePrefix'

    def prune_flags( self ):
        return 'flags'

    def prune_keep( self ):
        return 'keep'



    def print( self ):
        print( self.show() )

    def show( self ):
        strYml = "config:"
        strYml += "  url           :" + self.url           + '\n'
        strYml += "  dry-run       :" + str( self.dryrun)  + '\n'
        strYml += "\n"

        for item in self.archive:
            strYml +=  "  postfixName   :" + self.getArchiveValue( item, self.postfixName()   )        + '\n'
            strYml +=  "  flags         :" + str( self.getArchiveValue( item, self.backup_flags()     ) ) + '\n'
            strYml +=  "  includes      :" + str( self.getArchiveValue( item, self.backup_includes()      ) ) + '\n'
            strYml +=  "  excludes      :" + str( self.getArchiveValue( item, self.backup_excludes()      ) ) + '\n'
            strYml +=  "  prefixName    :" + self.getArchiveValue( item, self.prefixName()    )        + '\n'
            strYml +=  "  exclude-files :" + str( self.getArchiveValue( item, self.backup_exclude_files() ) ) + '\n'
            strYml +=  "    prune prefix:" + str( self.getPruneValue  ( item, self.prune_usePrefix() ) ) + '\n'
            strYml +=  "     keep       :" + str( self.getPruneValue  ( item, self.prune_keep()     ) ) + '\n'
            strYml +=  '  -----------------------------------------------------\n'
        return strYml

