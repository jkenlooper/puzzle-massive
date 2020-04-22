export interface ClaimBitResponse {
  message: string;
  name: string;
}
export class ChooseBitService {
  constructor() {}

  getBits(limit: number): Promise<string[]> {
    return fetch(`/newapi/choose-bit/?limit=${limit}`, {
      method: "GET",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
      },
    }).then(function (response: Response) {
      if (!response.ok) {
        throw new Error(response.statusText);
      }
      return response.json().then((response: any) => {
        return response.data.slice(0, limit);
      });
    });
  }

  claimBit(bit: string): Promise<ClaimBitResponse> {
    const params = new URLSearchParams();
    params.append("icon", bit);
    const request = new Request(`/newapi/claim-bit/?${params}`, {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
      },
    });

    return fetch(request).then((response: Response) => {
      if (!response.ok && response.status >= 500) {
        return Promise.reject({
          message: response.statusText,
          name: response.status + "",
        });
      }

      return response.json().then((data: ClaimBitResponse) => {
        if (!response.ok) {
          if (!data["message"]) {
            return Promise.reject({
              message: response.statusText,
              name: response.status + "",
            });
          } else {
            return Promise.reject(data);
          }
        } else {
          return data;
        }
      });

      //return response.text();
    });
  }
}

export const chooseBitService = new ChooseBitService();
