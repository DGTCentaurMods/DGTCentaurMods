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
from chess.engine import PovScore

from typing import List, Tuple, Callable, Optional, Dict, Union

import time, threading, queue, os, chess, chess.engine, asyncio


class TAnalyseResult():

    def __init__(self, uci_move:str, score:PovScore):
        self._uci_move = uci_move
        self._score = score

    @property
    def uci_move(self) -> str:
        return self._uci_move

    @property
    def score(self) -> PovScore:
        return self._score
    
    def __repr__(self) -> str:
        return f'TAnalyseResult("{self._uci_move}",{self._score})'


TPlayResult = chess.engine.PlayResult


# Wrapper intercepts inner engine exceptions that could occur...
class ChessEngineWrapper():

    __engine = None
    __engine_options = None

    __cache = []

    #__analysis_engine = None
    #__new_analysis_requested:bool = False

    __q = None
    __worker = None

    __running = False
    
    def __init__(self, engine_path:str, async_mode:bool = True):

        assert engine_path != None, "Need an engine_path!"

        self.__engine_path = engine_path

        # Async mode
        if async_mode:

            self.__q = queue.Queue()

            # Turn-on the engine worker thread
            self.__worker = threading.Thread(target=self.__engine_worker, daemon=True)
            
            self.__running = True
            
            self.__worker.start()

    def __engine_worker(self):
        while self.__running:
            #item = self.__q.get(block=True)

            if self.__q.empty() == False:

                try:
                    # We run the play or analyse request
                    task = self.__q.get()

                    fen = task["fen"]
                    cached = task["cached"]

                    # We only run the very last operation
                    # We also check if the task is not outdated comparing the FENs
                    #if self.__q.empty() and task["fen"] == task["board"].fen():
                    if fen == task["board"].fen():

                        # Cached result?
                        if cached:
                            cached_result = list(filter(lambda item:item["fen"] == fen, self.__cache))

                            if not len(cached_result):

                                # That task can take a while...
                                # We need to be sure the board did not change...

                                result = task["resultor"]()

                                self.__cache.pop()
                                self.__cache.insert(0, {
                                    "fen":fen,
                                    "result":result,
                                })
                            
                            else:
                                result = cached_result[0]["result"]
                        
                        else:
                            result = task["resultor"]()

                        # We only run the very last operation
                        # We also check if the task is not outdated comparing the FENs
                        #if self.__q.empty() and task["fen"] == task["board"].fen():
                        if fen == task["board"].fen():

                            task["callback"](result)

                        else:
                            Log.debug("Chess engine result ignored because outdated!")
                    else:
                        Log.debug("Chess engine operation cancelled because outdated!")

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
            
            self.__running = False
            self.__engine = None

            if self.__worker:
                self.__worker.join()

            self.__cache.clear()

        except Exception as e:
            Log.exception(ChessEngineWrapper.__quit_engine, e)
            pass

    def __instanciate_engine(self):

        try:

            if not self.__engine:

                self.__cache.clear()

                # 5 analysis can be cached
                for _ in range(5):
                    self.__cache.append({"fen":None})

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

    def __process(self, function_invoker:Union[Callable[[],Tuple[TAnalyseResult, ...]], Callable[[],TPlayResult]]) -> Union[Tuple[TAnalyseResult, ...], TPlayResult]:

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
                self.__engine.quit()
            except:
                pass

            # Another try with a FRESH engine!
            Log.debug("And let's retry with a fresh engine!")
            self.__engine = None

            time.sleep(.5)

    def configure(self, engine_options = {}) -> None:

        # Only for RodentIV...
        if "PersonalityFile" in engine_options:

            #engine_options["Verbose"] = consts.VERBOSE_CHESS_ENGINE

            # We replace the PersonalityFile tag by the Personality one
            # Taking the filename as personality name
            engine_options["Personality"] = common.capitalize_string(Path(engine_options["PersonalityFile"]).stem)

            del engine_options["PersonalityFile"]

        self.__engine_options = engine_options
    
    def analyse(self, board, limit, multipv=1, on_analyse_done:Optional[Callable[[Tuple[TAnalyseResult, ...]], None]] = None) -> Optional[Tuple[TAnalyseResult, ...]]:
        def _analyse(board, limit, multipv) -> Tuple[TAnalyseResult, ...]:
            try:
                self.__instanciate_engine()

                if self.__engine != None:
                    result = self.__engine.analyse(board=board, limit=limit, multipv=multipv)

                    #Log.debug(result)

                    # We convert to list anyway
                    if not type(result) is list:
                        result = [result]

                    return tuple(TAnalyseResult(str(info.get("pv")[0]), info.get("score")) for info in result)

            except Exception as e:
                Log.exception(ChessEngineWrapper.analyse, e)
                pass

            return None
        
        def resultor() -> Tuple[TAnalyseResult, ...]:
            return self.__process(lambda:_analyse(board=board, limit=limit, multipv=multipv))

        if self.__q:
            # Asynchronous mode
            return self.__q.put({"fen":board.fen(), "board":board, "cached":True, "resultor":resultor, "callback":on_analyse_done})
        else:
            # Direct sync mode
            return resultor()


    def play(self, board, limit, on_move_done:Optional[Callable[[TPlayResult], None]] = None) -> Optional[TPlayResult]:

        def _play(board, limit) -> TPlayResult:
            try:
                self.__instanciate_engine()

                if self.__engine != None:
                    return self.__engine.play(board=board, limit=limit)

            except Exception as e:
                Log.exception({ChessEngineWrapper.play}, e)
                pass

            return None
        
        def resultor() -> Optional[TPlayResult]:
            return self.__process(lambda:_play(board=board, limit=limit))

        if self.__q:
            # Asynchronous mode
            return self.__q.put({"fen":board.fen(), "board":board, "cached":False, "resultor":resultor, "callback":on_move_done})
        else:
            # Direct sync mode
            return resultor()

    def quit(self):
        self.__quit_engine()


def get(uci_path, async_mode = True):
    return ChessEngineWrapper(uci_path, async_mode)



'''
    def launch_analysis(self, board, limit, multipv,

                on_analysis:Callable[[PovScore, List[Move]], bool],
                on_analysis_ended:Callable[[int], None],
                
                engine_name:Optional[str]=None):
         
        async def _analysis() -> None:
            try:

                self.__new_analysis_requested = True

                while self.__analysis_engine:
                    time.sleep(.1)

                self.__new_analysis_requested = False

                _, self.__analysis_engine = await chess.engine.popen_uci(
                    consts.ENGINES_DIRECTORY+'/'+engine_name if engine_name else self.__engine_path)

                if self.__analysis_engine:

                    if self.__engine_options != None:

                        Log.debug(self.__engine_options)
                        await self.__analysis_engine.configure(self.__engine_options)

                    Log.debug("Launching analysis...")
   
                    with await self.__analysis_engine.analysis(board, limit=limit, multipv=multipv) as analysis:
                        async for info in analysis:
                            score:PovScore = info.get("score")
                            pv = info.get("pv")

                            #Log.debug(info)

                            if self.__new_analysis_requested:
                                Log.debug(f"New analysis requested - Stopping current one...")
                                analysis.stop()
                                break 

                            if pv:
                                if not on_analysis(score, pv):
                                    Log.debug(f"Plugin asked - Stopping analysis...")
                                    analysis.stop()
                                    break
                            
                            seldepth = info.get("seldepth", 10)

                            # Arbitrary stop condition.
                            if seldepth > limit.depth:
                                Log.debug(f"seldepth={seldepth} - Stopping analysis...")
                                analysis.stop()
                                break

                    await self.__analysis_engine.quit()
                    Log.debug(f"Analysis stopped.")
                    on_analysis_ended(0)

                    self.__analysis_engine = None

            except Exception as e:
                self.__analysis_engine = None
                Log.exception(ChessEngineWrapper.launch_analysis, e)
                on_analysis_ended(1)
                pass

        asyncio.run(_analysis())
    '''