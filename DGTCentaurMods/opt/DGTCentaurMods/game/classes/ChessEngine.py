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

from DGTCentaurMods.game.classes import Log

import time, threading, queue
import chess, chess.engine

# Wrapper intercepts inner engine exceptions that could occur...
class _ChessEngine():

    __engine = None
    __engine_options = None

    __q = None
    __worker = None
    __on_taskengine_done = None

    __destroyed = False
    
    def __init__(self, engine_path, on_taskengine_done = None):

        assert engine_path != None, "Need an engine_path!"

        self.__engine_path = engine_path
        self.__on_taskengine_done = on_taskengine_done

        # Async mode
        if on_taskengine_done:

            assert callable(on_taskengine_done), "'on_taskengine_done' has to be a function!"

            self.__q = queue.Queue()

            # Turn-on the enfine worker thread
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
                    if self.__q.empty() and task["fen"] == task["board"].fen():

                        # That task can take a while...
                        # We need to be sure the board did not change...
                        result = task["resultor"]()

                        # We only run the very last operation
                        # We also check if the task is not outdated comparing the FENs
                        if (self.__q.empty() and task["fen"] == task["board"].fen()):

                            self.__on_taskengine_done(result)

                        else:
                            Log.debug("_ChessEngine.__engine_worker : Async operation cancelled.")

                    self.__q.task_done()

                except Exception as e:
                    Log.exception(f"_ChessEngine.__engine_worker error:{e}")
                    pass

            time.sleep(.5)

    def __instanciate(self):

        try:
            self.__engine = None
            self.__engine = chess.engine.SimpleEngine.popen_uci(self.__engine_path)
            
            Log.debug(f'_ChessEngine.__instanciate({id(self.__engine)})')
            
            if self.__engine_options != None:
                self.__engine.configure(self.__engine_options)

        except Exception as e:
            Log.exception(f"_ChessEngine.__instanciate error:{e}")
            self.__engine = None
            pass

    def __process(self, function_invoker):

        # 3 retries
        for _ in range(1,3):

            result = function_invoker()

            if result != None:
                return result
            
            # Failure...
            # We try anyway to quit the current engine...
            try:
                self.__engine.quit()
            except:
                pass

            # Another try with a FRESH engine!
            self.__engine == None

            time.sleep(.5)

    def configure(self, engine_options = None):

        self.__engine_options = engine_options

    def analyse(self, board, limit):

        def _analyse(board, limit):
            try:
                if self.__engine == None:
                    self.__instanciate()

                if self.__engine != None:
                    return self.__engine.analyse(board=board, limit=limit)

            except Exception as e:
                Log.exception(f"_ChessEngine.analyse error:{e}")
                pass

            return None
        
        def resultor():
            return self.__process(lambda:_analyse(board=board, limit=limit))

        if self.__q:
            self.__q.put({"fen":board.fen(), "board":board, "resultor":resultor})
        else:
            return resultor()


    def play(self, board, limit, info):

        def _play(board, limit, info):
            try:
                if self.__engine == None:
                    self.__instanciate()

                if self.__engine != None:
                    return self.__engine.play(board=board, limit=limit, info=info)

            except Exception as e:
                Log.exception(f"_ChessEngine.play error:{e}")
                pass

            return None
        
        def resultor():
            return self.__process(lambda:_play(board=board, limit=limit, info=info))

        if self.__q:
            # Async mode
            self.__q.put({"fen":board.fen(), "board":board, "resultor":resultor})
        else:
            # Direct sync mode
            return resultor()

    def quit(self):

        try:
            if self.__engine != None:

                Log.debug(f'_ChessEngine.quit({id(self.__engine)})')
                self.__engine.quit()
            
            self.__destroyed = True

            if self.__worker:
                self.__worker.join()

        except Exception as e:
            Log.exception(f"_ChessEngine.quit error:{e}")
            pass

def get(uci_path, on_taskengine_done = None):
    return _ChessEngine(uci_path, on_taskengine_done)
