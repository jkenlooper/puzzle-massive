import FetchService from "./fetch.service";

type UserDetailsCallback = () => any;

interface UserDetailsResponse {
  bit_expired?: boolean;
  cookie_expires?: string;
  dots: number;
  icon?: string;
  id?: number;
  login?: string;
  score: number;
}
interface UserDetailsData extends UserDetailsResponse {
  hasBit: boolean;
}

function claimRandomBit(): Promise<void> {
  return fetch("/newapi/claim-random-bit/", {
    method: "POST",
  }).then((response: Response) => {
    if (!response.ok) {
      throw new Error(response.statusText);
    }
  });
}

interface AnonymousLoginResponse {
  bit: string;
}
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
  };

  constructor() {
    this.updateUserDetails()
      .then(() => {
        this._broadcast();
      })
      .finally(() => {
        this.hasInitialized = true;
      });
    document.addEventListener(
      "userDetailsChange",
      this._onUserDetailsChange.bind(this)
    );
  }

  generateAnonymousLogin() {
    return generateAnonymousLogin.get<AnonymousLoginResponse>();
  }

  updateUserDetails(notClaimRandomBit: boolean = false): Promise<void> {
    return fetch("/newapi/current-user-id/")
      .then((response: Response) => {
        if (!response.ok) {
          throw new Error(response.statusText);
        }
      })
      .then(() => {
        // get the new user details from server
        return fetch("/newapi/user-details/")
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
              userDetails
            );
            if (!hasBit && !notClaimRandomBit) {
              // Set a random bit icon.
              return claimRandomBit().then(() => {
                // Prevent endlessly trying to pick a random bit icon if none are available
                return this.updateUserDetails(true);
              });
            } else {
              return;
            }
          });
      });
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
