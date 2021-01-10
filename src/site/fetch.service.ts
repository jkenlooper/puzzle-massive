class FetchService {
  url: string;

  constructor(url: string) {
    this.url = url;
  }

  getText(): Promise<string> {
    return fetch(this.url, {
      method: "GET",
      credentials: "same-origin",
      headers: {
        "Content-Type": "text/html",
      },
    }).then((response: Response) => {
      if (!response.ok) {
        throw new Error(response.statusText);
      }
      return response.text();
    });
  }

  get<T>(): Promise<T> {
    return fetch(this.url, {
      method: "GET",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
      },
    }).then((response: Response) => {
      if (!response.ok) {
        throw new Error(response.statusText);
      }
      return response.json().then((response: T) => {
        return response;
      });
    });
  }

  postForm<T>(data): Promise<T> {
    return fetch(this.url, {
      method: "POST",
      credentials: "same-origin",
      body: data,
    }).then((response: Response) => {
      if (!response.ok && response.status >= 500) {
        return Promise.reject({
          message: response.statusText,
          name: response.status + "",
        });
      }
      return response.json().then((data: T) => {
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
    });
  }

  patch<T>(data, headers?): Promise<T> {
    const _headers = {
      "Content-Type": "application/json",
    };
    if (headers) {
      Object.assign(_headers, headers);
    }
    return fetch(this.url, {
      method: "PATCH",
      credentials: "same-origin",
      headers: _headers,
      body: JSON.stringify(data),
    }).then((response: Response) => {
      if (!response.ok) {
        throw new Error(response.statusText);
      }
      return response.json().then((response: T) => {
        return response;
      });
    });
  }
}

export default FetchService;
