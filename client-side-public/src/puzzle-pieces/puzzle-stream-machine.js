import { createMachine } from "@xstate/fsm";
import { puzzleStreamMachineDefinition } from "./puzzle-stream-machine-definition";
export {
  RECONNECT_INTERVAL,
  RECONNECT_TIMEOUT,
} from "./puzzle-stream-machine-definition";
export const puzzleStreamMachine = createMachine(puzzleStreamMachineDefinition);
