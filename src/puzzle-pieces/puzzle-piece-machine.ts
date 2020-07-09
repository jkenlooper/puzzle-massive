// TODO: WIP
import { createMachine } from "@xstate/fsm";
import { puzzlePieceMachineDefinition } from "./puzzle-piece-machine-definition";

type PuzzlePieceState =
  | {
      value: "unknown";
      context: PuzzlePieceContext;
    }
  | {
      value: "active";
      context: PuzzlePieceContext;
    }
  | {
      value: "pending";
      context: PuzzlePieceContext;
    }
  | {
      value: "immovable";
      context: PuzzlePieceContext;
    }
  | {
      value: "queued";
      context: PuzzlePieceContext;
    }
  | {
      value: "movable";
      context: PuzzlePieceContext;
    };

type PuzzlePieceEvent =
  | {
      type: "INIT";
    }
  | {
      type: "SOMETHING";
    };
interface PuzzlePieceContext {}

export const puzzlePieceMachine = createMachine<
  PuzzlePieceContext,
  PuzzlePieceEvent,
  PuzzlePieceState
>(puzzlePieceMachineDefinition);
