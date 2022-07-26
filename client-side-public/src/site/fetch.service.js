class FetchService {
  constructor(url) {
    this.url = url;
  }
  getText() {
    return fetch(this.url, {
      method: "GET",
      credentials: "same-origin",
      headers: {
        "Content-Type": "text/html",
      },
    }).then((response) => {
      if (!response.ok) {
        throw new Error(response.statusText);
      }
      return response.text();
    });
  }
  get(headers) {
    const _headers = {
      "Content-Type": "application/json",
    };
    if (headers) {
      Object.assign(_headers, headers);
    }
    return fetch(this.url, {
      method: "GET",
      credentials: "same-origin",
      headers: _headers,
    }).then((response) => {
      if (!response.ok) {
        throw new Error(response.statusText);
      }
      return response.json().then((response) => {
        return response;
      });
    });
  }
  postForm(data) {
    return fetch(this.url, {
      method: "POST",
      credentials: "same-origin",
      body: data,
    }).then((response) => {
      if (!response.ok && response.status >= 500) {
        return Promise.reject({
          message: response.statusText,
          name: response.status + "",
        });
      }
      return response.json().then((data) => {
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
  patch(data, headers) {
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
    }).then((response) => {
      if (!response.ok) {
        throw new Error(response.statusText);
      }
      return response.json().then((response) => {
        return response;
      });
    });
  }
  patchNoContent(data, headers) {
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
    }).then((response) => {
      if (!response.ok) {
        return response.json().then((body) => {
          return Promise.reject({
            body: body,
            status: response.status,
          });
        });
      }
      if (response.status === 204) {
        return Promise.resolve();
      }
      throw new Error(response.statusText);
    });
  }
}
export default FetchService;
