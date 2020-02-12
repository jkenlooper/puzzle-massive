// TODO: WIP
import { createMachine } from "@xstate/fsm";

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
>({
  id: "puzzle-piece",
  initial: "unknown",
  context: {},
  states: {
    unknown: {},
    active: {},
    pending: {},
    immovable: {},
    queued: {},
    movable: {},
  },
});
