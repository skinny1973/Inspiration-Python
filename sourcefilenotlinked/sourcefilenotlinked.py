#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

import os, getopt
import sys
import sqlite3
import datetime

## @brief Classe per la ricerca nel FS dei files di sorgenti che non vengono utilizzati
#  @author Daniele Franceschini
#  @details
#  @version: 0.2
#  @date 2013-02-01
#  @pre Installazione di Python
#  @bug
#  @warning
#  @copyright

class searchFile():
    #example rapameters: -l -x asp,js,asa,css -e test Z:\svn\trunk\source
    #example rapameters: --log --extensions asp,js,asa,css --exclude "test" Z:\svn\trunk\source
    #complete example: python searchfilenotused.py -l -x asp,js,asa,css -e test Z:\svn\trunk\source

    ## @var _fileListPath
    #  Lista che contiene l'elenco dei percorsi dei file che devono essere verificati
    _fileListPath = []

    ## @var _fileList
    #  Lista che contiene l'elenco dei nomi dei file che devono essere verificati
    _fileList = []

    ## @var _rootdir
    #  Variabile privata che contiene il percorso su cui viene fatta la ricerca dei files
    _rootdir = ""

    ## @var _cn
    #  Connessione al database
    _cn = None

    ## @var _cursor
    #  Cursorse per l'interrogazione dei dati
    _cursor = None

    ## @var _extensions
    #  Lista che contiene le estensioni dei files che devono essere prese in considerazione dalla ricerca
    _extensions = None

    ## @var _excludeFolderList
    #  Lista che contiene le cartelle che devono essere escluse dalla ricerca
    _excludeFolderList = []

    ## @var _script_name
    #  Contiene il nome dello script
    _script_name = []

    ## @var _db_name
    #  Contiene il nome del db
    _db_name = []

    ## @var _verbose
    #  Indica se deve essere mostrato un output durante l'esecuzione dello script
    _verbose = False

    ## @var _force
    #  Forza l'esecuzione del script saltando i controlli sulle esecuzioni precedenti
    _force = False

    ## Costruttore.
    # Lettura delle opzioni e degli argomenti della riga di comando.
    # L'opzione che pu&ograve; essere passata allo script e la seguente:
    # @li"-e" o "-\-exclude" @n con affianco l'elenco delle directory che devono essere
    # escluse dalla rca es.: @code python searchfilenotused.py -e "usa,ita,fra,chn,deu,ita,esp,rus,jpn" @endcode
    # oppure
    # @code python searchfilenotused.py -exclude "usa,ita,fra,chn,deu,ita,esp,rus,jpn" @endcode
    # @li L'argomento è obbligatorio per questo comando e contiene il percorso su cui fare la ricerca
    # es.: @code python searchfilenotused.py Z:\svn\trunk\source @endcode
    # oppure @code python searchfilenotused.py Z:\svn\trunk\source @endcode
    def __init__(self):
        try:
            #sys.argv = "xxx.py -e test /home/daniele/Documenti".split()
            opts, args = getopt.getopt(sys.argv[1:], 'hlvx:e:', ['help','log','verbose','extensions=','exclude='])

        except getopt.GetoptError as err:
            # print help information and exit:
            print str(err) # will print something like "option -a not recognized"
            sys.exit(2)

        for o, a in opts:
            if o in ("-h", "--help"):
                print "Use: sourcefilenotlinked [OPTIONS] directory name where the research need to be made\n"
                print "   -l, --log\t\tMake a log file where listed the results"
                print "   -v, --verbose\tShow on terminal every single step"
                print "   -x, --extensions\tNeed a argument that indicates the file extension to be consider in research"
                print "   -e, --exclude\tNeed a argument that indicates the directory to exclude from research\n"
                sys.exit(2)

            elif o in ("-e", "--exclude"):
                self._excludeFolderList = str(a).split(",")
            elif o in ("-x", "--extensions"):
                self._extensions = str(a).split(",")
            elif o in ("-v", "--verbose"):
                self._verbose = True
            elif o in ("-l", "--log"):
                self._force = True
            else:
                assert False, "unhandled option"

        if len(args) == 0:
            print "Specify the research path"
            sys.exit(2)

        self._rootdir = args[0]

        #costruisco correttamente i percorsi con le cartelle indicate
        for i in self._excludeFolderList:
            self._excludeFolderList[self._excludeFolderList.index(i)] = os.path.join(self._rootdir, i)

        #prendo il nome dello script e lo uso per nominare il file del db
        self._script_name = os.path.basename(__file__).split(".")
        self._db_name = self._script_name[0] + ".db"

        #chiamo il db con lo stesso nome dello script
        self.__openDB(self._db_name)
        if self._force:
            self.start()
        else:
            self.__searchPreviousResult()

    ## Questa funzione prevede anche la gestione di un piccolo db per evitare di perdere i risultati di recenti ricerche,
    # inoltre grazie al db i dati possono essere spostati e gestiti
    def __openDB(self,db):
        #se il db non esiste lo creo e lo popolo con le tabelle che mi servono
        if not os.path.exists(db):
            self._cn = sqlite3.connect(db)
            self._cursor = self._cn.cursor()
            self._cn.execute("CREATE TABLE 'file_found' ('file_name' VARCHAR, 'found_in' VARCHAR)")
            self._cn.execute("CREATE TABLE 'file_not_found' ('file_name' VARCHAR)")
        else:
            #apro il db
            self._cn = sqlite3.connect(db)
            self._cursor = self._cn.cursor()

    ## Funzione che controlla se l'utente desidera vedere il risultato
    #  di una precedente ricerca invece di farne una nuova
    def __searchPreviousResult(self):
        self._cursor.execute("select * from file_not_found")
        rows = self._cursor.fetchall()
        if len(rows) == 0:
            self.start()
        else:
            out = raw_input("There are results of previous research, do you want see them? (Y/N)")
            if out == "y" or out == "Y":
                print "\nList file not found in previous research"
                for row in rows:
                    print row[0]
            else:
                self._cn.close()
                os.remove(self._db_name)
                self.__openDB(self._db_name)
                self.start()

    ## Funzione che inserisce nel db l'elenco dei files che sono stati
    #  trovati all' interno dei sorgenti e dove @b sono stati trovati
    #  @param file_name
    #  @param file_host
    def __insert_file_found(self, file_name, file_host):
        sql = 'insert into file_found values (?, ?)'
        for file in file_host:
            self._cursor.execute(sql, (file_name, str(file)))
        self._cn.commit()

    ## Funzione che inserisce nel db l'elenco dei files che <b>non sono</b> stati
    #  trovati all' interno dei sorgenti
    #  @param file_name
    def __insert_file_not_found(self, file_name):
        for file in file_name:
            sql = "insert into file_not_found values('" + file + "')"
            self._cursor.execute(sql)
        self._cn.commit()

    ## Questo metodo esegue la ricerca sul FS per cercare eventuali file che non sono
    #  pi&ugrave; utilizzati all' interno dei sorgenti
    def start(self):
        found_something = False
        print "Loading file ..."

        #Carico tutti i files presenti nel persorso indicato negli argomenti (self._rootdir)
        for root, subFolders, files in os.walk(self._rootdir):
            #Escludo dalla ricerca tutte le directory che non sono state indicate negli argomenti (self._excludeFolderList)
            exclude = False

            for i in range(len(self._excludeFolderList)):
               # exclude_folder = set(self._excludeFolderList[i].split("\\"))
                exclude_folder = tuple(self._excludeFolderList[i].split("/"))
                #current_folder = root.split("\\")
                current_folder = tuple(root.split("/"))
                #current_folder = set(current_folder[0:len(exclude_folder)])
                #Faccio questa operazione per escludere anche le sottocartelle delle cartelle da escludere
                current_folder = tuple(current_folder[0:len(exclude_folder)])

                if current_folder == exclude_folder:
                    exclude = True
                    break
                else:
                    exclude = False

            if not exclude:
                for file in files:
                    #Seleziono solo i file sorgente
                    if self._extensions is not None:
                        for ex in self._extensions:
                            if file.endswith(ex):
                                #Metto in memoria i files che sono soggetti al controllo dei sorgenti
                                self._fileListPath.append(os.path.join(root,file))
                                self._fileList.append(file)
                                break
                    else:
                        self._fileListPath.append(os.path.join(root,file))
                        self._fileList.append(file)


        #preparo un paio di liste in cui carico gli esiti delle ricerche
        file_not_found = []
        file_found = []

        #flag che indica se ho trovato qualcosa (found = 1)
        found = 0

        i = 0
        if len(self._fileList) > 0:
            print "start searching"
            for filename in self._fileList:
                if self._verbose:
                    print "Check file " + filename
                else:
                    progress = float(float((i + 1) * 100) / len(self._fileList))

                    sys.stdout.write("Searching progress: %f%%   \r" % progress)
                    sys.stdout.flush()

                current_file = self._fileListPath[i]
                i += 1

                for file in self._fileListPath:
                    #inizio la ricerca in tutti i files che ho trovato nel FS
                    try:
                        #apro il file per frugare nel sorgente
                        searchfile = open(file, "r")
                        #print "source:\n\t"
                        for line in searchfile:
                            #print line
                            if str(filename) in line:
                                file_found.append(file)
                                found = 1
                                break
                    except IOError:
                        print IOError.message
                    finally:
                        searchfile.close()
                        #print "end file\n\n"

                if found == 1:
                    #se ho trovato qualcosa lo registro nel db
                    self.__insert_file_found(filename, file_found)
                    #stampo anche a video il risultato corrente della ricerca
                    #print "This file exist in (" + str(file_found) + ")"
                    file_found = []

                if found == 0:
                    found_something = True
                    #se non ho trovato niente memorizzo il percorso del file
                    file_not_found.append(current_file)

                    if self._verbose:
                        #stampo a video anche le ricerche che non hanno trovato niente
                        print "This file doesn't exist (" + str(filename) + ")"

                found = 0

            #metto nel db i files che non sono stati trovati nei sorgenti
            self.__insert_file_not_found(file_not_found)

            #stampo a video un sommario
            print "\nSummary file not found:"
            if self._force:
                try:
                    l = open(self._script_name[0] + ".log", "a")

                    try:
                        dt = datetime.datetime.now()
                        l.write(str(dt) + "\n")
                        for f in file_not_found:
                            l.write(f + "\n")
                        l.write("\n")
                        print "Unexpected error:", sys.exc_info()[0]
                    finally:
                        l.close()
                except IOError:
                    print IOError.message

            for f in file_not_found:
                print str(f)

        else:
            print "no files found"

        if self._cn:
            self._cn.close()

        return found_something

sf = searchFile()