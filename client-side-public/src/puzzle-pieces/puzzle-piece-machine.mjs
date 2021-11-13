// TODO: WIP
import xstate from "@xstate/fsm";
import puzzlePieceMachineDefinition from "./puzzle-piece-machine-definition.mjs";

const puzzlePieceMachine = xstate.createMachine(puzzlePieceMachineDefinition);
export default puzzlePieceMachine;
