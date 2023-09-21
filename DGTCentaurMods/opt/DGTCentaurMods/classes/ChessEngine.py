# This file is part of the DGTCentaur Mods open source software
# ( https://github.com/Alistair-Crompton/DGTCentaurMods )
#
# DGTCentaur Mods is free software: you can redistribute
# it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# DGTCentaur Mods is distributed in the hope that it will
# be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this file.  If not, see
#
# https://github.com/Alistair-Crompton/DGTCentaurMods/blob/master/LICENSE.md
#
# This and any other notices must remain intact and unaltered in any
# distribution, modification, variant, or derivative of this software.

from DGTCentaurMods.classes import Log
from DGTCentaurMods.consts import consts
from DGTCentaurMods.lib import common

from pathlib import Path

import time, threading, queue, os, chess, chess.engine


# Wrapper intercepts inner engine exceptions that could occur...
class ChessEngineWrapper():

    __engine = None
    __engine_options = None

    __q = None
    __worker = None

    __destroyed = False
    
    def __init__(self, engine_path, async_mode = True):

        assert engine_path != None, "Need an engine_path!"

        self.__engine_path = engine_path

        # Async mode
        if async_mode:

            self.__q = queue.Queue()

            # Turn-on the engine worker thread
            self.__worker = threading.Thread(target=self.__engine_worker, daemon=True)
            self.__worker.start()

    def __engine_worker(self):
        while self.__destroyed == False:
            #item = self.__q.get(block=True)

            if self.__q.empty() == False:

                try:
                    # We run the play or analyse request
                    task = self.__q.get()

                    # We only run the very last operation
                    # We also check if the task is not outdated comparing the FENs
                    #if self.__q.empty() and task["fen"] == task["board"].fen():
                    if task["fen"] == task["board"].fen():

                        # That task can take a while...
                        # We need to be sure the board did not change...
                        result = task["resultor"]()

                        # We only run the very last operation
                        # We also check if the task is not outdated comparing the FENs
                        #if self.__q.empty() and task["fen"] == task["board"].fen():
                        if task["fen"] == task["board"].fen():

                            task["callback"](result)

                        else:
                            Log.debug("Async engine result ignored because outdated!")
                    else:
                        Log.debug("Async engine operation cancelled because outdated!")

                    self.__q.task_done()

                except Exception as e:
                    Log.exception(ChessEngineWrapper.__engine_worker, e)
                    pass

            time.sleep(.5)

    def __quit_engine(self):

        try:
            if self.__engine != None:

                Log.debug(f'{ChessEngineWrapper.__quit_engine.__name__}({id(self.__engine)})')
                self.__engine.quit()
            
            self.__destroyed = True

            if self.__worker:
                self.__worker.join()

        except Exception as e:
            Log.exception(ChessEngineWrapper.__quit_engine, e)
            pass

    def __instanciate_engine(self):

        try:
            # Only for RodentIV...
            os.environ["RODENT4PERSONALITIES"] = consts.ENGINES_DIRECTORY+'/personalities'
            os.environ["RODENT4BOOKS"] = consts.ENGINES_DIRECTORY+'/books'

            self.__engine = None
            self.__engine = chess.engine.SimpleEngine.popen_uci(self.__engine_path)
            
            Log.debug(f'{ChessEngineWrapper.__instanciate_engine.__name__}({id(self.__engine)})')
            
            if self.__engine_options != None:

                Log.debug(self.__engine_options)
                self.__engine.configure(self.__engine_options)

        except Exception as e:
            Log.exception(ChessEngineWrapper.__instanciate_engine, e)
            self.__engine = None
            pass

    def __process(self, function_invoker):

        # 3 retries
        for _ in range(0,3):

            try:
                result = function_invoker()
            except:
                result = None

            if result:
                return result
            
            # Failure...
            # We try anyway to quit the current engine...
            try:
                Log.debug("Trying properly stopping engine...")
                self.__engine.quit()
            except:
                pass

            # Another try with a FRESH engine!
            Log.debug("And let's retry with a fresh engine!")
            self.__engine = None

            time.sleep(.5)

    def configure(self, engine_options = {}):

        # Only for RodentIV...
        if "PersonalityFile" in engine_options:

            #engine_options["Verbose"] = consts.VERBOSE_CHESS_ENGINE

            # We replace the PersonalityFile tag by the Personality one
            # Taking the filename as personality name
            engine_options["Personality"] = common.capitalize_string(Path(engine_options["PersonalityFile"]).stem)

            del engine_options["PersonalityFile"]

        self.__engine_options = engine_options

    def analyse(self, board, limit, on_taskengine_done = None):

        def _analyse(board, limit):
            try:
                if self.__engine == None:
                    self.__instanciate_engine()

                if self.__engine != None:
                    return self.__engine.analyse(board=board, limit=limit)

            except Exception as e:
                Log.exception(ChessEngineWrapper.analyse, e)
                pass

            return None
        
        def resultor():
            return self.__process(lambda:_analyse(board=board, limit=limit))

        if self.__q:

            assert callable(on_taskengine_done), "'on_taskengine_done' has to be a function!"

            # Async mode
            self.__q.put({"fen":board.fen(), "board":board, "resultor":resultor, "callback":on_taskengine_done})
        else:
            # Direct sync mode
            return resultor()


    def play(self, board, limit, info, on_taskengine_done = None):

        def _play(board, limit, info):
            try:
                if self.__engine == None:
                    self.__instanciate_engine()

                if self.__engine != None:
                    return self.__engine.play(board=board, limit=limit, info=info)

            except Exception as e:
                Log.exception({ChessEngineWrapper.play}, e)
                pass

            return None
        
        def resultor():
            return self.__process(lambda:_play(board=board, limit=limit, info=info))

        if self.__q:

            assert callable(on_taskengine_done), "'on_taskengine_done' has to be a function!"

            # Async mode
            self.__q.put({"fen":board.fen(), "board":board, "resultor":resultor, "callback":on_taskengine_done})
        else:
            # Direct sync mode
            return resultor()

    def quit(self):
        self.__quit_engine()


def get(uci_path, async_mode = True):
    return ChessEngineWrapper(uci_path, async_mode)
