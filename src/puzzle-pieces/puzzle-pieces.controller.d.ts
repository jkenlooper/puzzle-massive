// import PuzzleService from "./puzzle-service.js";

declare class PuzzlePiecesController {
  $container: HTMLElement;
  $karmaStatus: HTMLElement;
  karmaStatusIsActiveTimeout: number;
  renderPieces: Function;
  status: any;
  parentoftopleft: number;
  puzzleId: string;
  pieceUpdateHandles: object;
  pieceRejectedHandles: object;
  instanceId: string;

  pieces: object;
  collection: Array<number>;
  piecesTimestamp: string;
  selectedPieces: Array<number>;
  karmaChange: number;
  karma: number;
  blocked: boolean;
  mark: string;

  isImmovable(pieceID: number): boolean;
  unSelectPiece(pieceID: number | null): void;
  selectPiece(pieceID: number | null): void;
  dropSelectedPieces(x: number, y: number, scale: number): void;
  moveBy(pieceID: number | null, x: number, y: number, scale: number): void;

  unsubscribe(): void;

  constructor(
    puzzleId: string,
    puzzleService: any, //PuzzleService,
    $container: HTMLElement,
    $karmaStatus: HTMLElement
  );
}

export = PuzzlePiecesController;
