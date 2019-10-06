import FetchService from "./fetch.service";

type UserDetailsCallback = () => any;

interface PuzzleInstanceItem {
  readonly front_url: string;
  readonly src: string;
}

export type PuzzleInstanceList = Array<PuzzleInstanceItem>;

interface UserDetailsResponse {
  bit_expired?: boolean;
  cookie_expires?: string;
  dots: number;
  icon?: string;
  id?: number;
  login?: string;
  score: number;
  can_claim_user?: boolean;
  readonly puzzle_instance_list?: PuzzleInstanceList;
  readonly user_puzzle_count: number;
  readonly puzzle_instance_count: number;
}
interface UserDetailsData extends UserDetailsResponse {
  hasBit: boolean;
  loginAgain: boolean;
  hasUserPuzzleSlots: boolean;
  hasAvailableUserPuzzleSlot: boolean;
  emptySlotCount: number;
  puzzleInstanceCount: number;
}

interface AnonymousLoginResponse {
  bit: string;
}
const baseUrl = `${window.location.protocol}//${window.location.host}`;
const generateAnonymousLogin = new FetchService(
  "/newapi/generate-anonymous-login/"
);

class UserDetailsService {
  hasInitialized: boolean = false;
  listeners: Map<string, UserDetailsCallback> = new Map();
  userDetails: UserDetailsData = {
    dots: 0,
    score: 0,
    hasBit: false,
    loginAgain: false,
    user_puzzle_count: 0,
    puzzle_instance_count: 0,
    hasUserPuzzleSlots: false,
    hasAvailableUserPuzzleSlot: false,
    emptySlotCount: 0,
    puzzleInstanceCount: 0,
  };
  static anonymousLoginName = "anonymous-login";
  static localUserId = "user-id";

  constructor() {
    if (!window.localStorage) {
      // User may have blocked the site from storing cookies and using
      // localStorage.
      return;
    }
    this.currentUserId().then((currentUserId) => {
      // verify locally saved bit login with id that comes back.  If it is
      // different then login again.
      const localUserId = window.localStorage.getItem(
        UserDetailsService.localUserId
      );
      if (localUserId && localUserId != currentUserId) {
        if (
          window.localStorage.getItem(UserDetailsService.anonymousLoginName)
        ) {
          this.userDetails.loginAgain = true;
        }
      }
      this.updateUserDetails(currentUserId)
        .then(() => {
          this._broadcast();
        })
        .finally(() => {
          this.hasInitialized = true;
        });
    });
    document.addEventListener(
      "userDetailsChange",
      this._onUserDetailsChange.bind(this)
    );
  }

  generateAnonymousLogin() {
    return generateAnonymousLogin.get<AnonymousLoginResponse>();
  }

  storeAnonymousLogin(anonymousLogin: string) {
    window.localStorage.setItem(
      UserDetailsService.anonymousLoginName,
      anonymousLogin
    );
    window.localStorage.setItem(
      UserDetailsService.localUserId,
      String(this.userDetails.id)
    );
  }

  forgetAnonymousLogin() {
    window.localStorage.removeItem(UserDetailsService.anonymousLoginName);
    window.localStorage.removeItem(UserDetailsService.localUserId);
  }

  get anonymousLoginLink(): string {
    return `${baseUrl}${window.localStorage.getItem(
      UserDetailsService.anonymousLoginName
    ) || ""}`;
  }

  currentUserId(): Promise<string> {
    return fetch("/newapi/current-user-id/", {
      method: "GET",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
      },
    }).then((response: Response) => {
      if (!response.ok) {
        throw new Error(response.statusText);
      }
      return response.text();
    });
  }

  updateUserDetails(
    currentUserId: string | undefined = undefined
  ): Promise<void> {
    if (!currentUserId) {
      return this.currentUserId().then(() => {
        return getUserDetails.call(this);
      });
    } else {
      return getUserDetails.call(this);
    }

    function getUserDetails() {
      // get the new user details from server
      return fetch("/newapi/user-details/", {
        method: "GET",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
        },
      })
        .then((response: Response) => {
          if (!response.ok) {
            throw new Error(response.statusText);
          }
          return response.json().then((response: UserDetailsResponse) => {
            return response;
          });
        })
        .then((userDetails) => {
          const hasBit = !!(userDetails.icon && userDetails.icon.trim());
          this.userDetails = Object.assign(
            {
              hasBit: hasBit,
            },
            userDetails,
            {
              loginAgain: this.userDetails.loginAgain,
              hasUserPuzzleSlots: !!userDetails.user_puzzle_count,
              hasAvailableUserPuzzleSlot: !!(
                userDetails.user_puzzle_count -
                userDetails.puzzle_instance_count
              ),
              emptySlotCount:
                userDetails.user_puzzle_count -
                userDetails.puzzle_instance_count,
              puzzleInstanceCount: userDetails.puzzle_instance_count,
            }
          );
          return;
        });
    }
  }

  _onUserDetailsChange(/*ev: Event*/) {
    this.updateUserDetails().then(() => {
      this._broadcast();
    });
  }

  _broadcast() {
    this.listeners.forEach((fn /*, id*/) => {
      fn();
    });
  }

  subscribe(fn: UserDetailsCallback, id: string) {
    //console.log("subscribe", fn, id);
    // Add the fn to listeners
    this.listeners.set(id, fn);
  }

  unsubscribe(id: string) {
    //console.log("unsubscribe", id);
    // remove fn from listeners
    this.listeners.delete(id);
  }
}

const userDetailsService = new UserDetailsService();
export default userDetailsService;
