// import PuzzleService from "./puzzle-service.js";

declare class PuzzlePiecesController {
  renderPieces: Function;
  puzzleId: string;
  pieceUpdateHandles: object;
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
    puzzleService: any //PuzzleService,
  );
}

export = PuzzlePiecesController;
