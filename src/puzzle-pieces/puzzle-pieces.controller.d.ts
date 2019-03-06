// import PuzzleService from "./puzzle-service.js";

declare class PuzzlePiecesController {
  $container: HTMLElement;
  alerts: object;
  $karmaStatus: HTMLElement;
  karmaStatusIsActiveTimeout: number;
  renderPieces: Function;
  status: any;
  parentoftopleft: number;
  puzzleid: string;
  pieceUpdateHandles: object;
  pieceRejectedHandles: object;

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

  constructor(
    puzzleService: any, //PuzzleService,
    divulgerService: any, //DivulgerService,
    $container: HTMLElement,
    alerts: any,
    $karmaStatus: HTMLElement
  );
}

export = PuzzlePiecesController;
