let refreshPromise = null;

export async function apiFetch(apiBaseUrl, path, options = {}, getTokens, setTokens, onAuthFailure) {
  const { accessToken, refreshToken } = getTokens() || {};
  const headers = new Headers(options.headers || {});

  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  const requestOptions = {
    ...options,
    headers,
  };

  const url = apiBaseUrl.replace(/\/+$/, "") + "/" + path.replace(/^\//, "");
  let response = await fetch(url, requestOptions);

  if (response.status !== 401) {
    return response;
  }

  if (!refreshToken) {
    onAuthFailure?.();
    return response;
  }

  // Deduplicate concurrent refreshes: if a refresh is already in-flight,
  // wait for it instead of starting a new one.
  if (!refreshPromise) {
    refreshPromise = (async () => {
      try {
        const refreshResponse = await fetch(`${apiBaseUrl.replace(/\/+$/, "")}/auth/refresh`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });

        if (!refreshResponse.ok) {
          onAuthFailure?.();
          throw new Error('refresh_failed');
        }

        const refreshData = await refreshResponse.json();
        const newAccessToken = refreshData.access_token;
        const newRefreshToken = refreshData.refresh_token;

        if (newAccessToken && newRefreshToken) {
          setTokens?.({ accessToken: newAccessToken, refreshToken: newRefreshToken });
          return { accessToken: newAccessToken, refreshToken: newRefreshToken };
        }

        onAuthFailure?.();
        throw new Error('refresh_bad_payload');
      } finally {
        refreshPromise = null;
      }
    })();
  }

  let refreshedTokens;
  try {
    refreshedTokens = await refreshPromise;
  } catch (e) {
    // Refresh failed (onAuthFailure already called inside the refresh); return original 401 response.
    return response;
  }

  const retryHeaders = new Headers(options.headers || {});
  if (refreshedTokens?.accessToken) {
    retryHeaders.set("Authorization", `Bearer ${refreshedTokens.accessToken}`);
  }

  const retryOptions = { ...options, headers: retryHeaders };

  return fetch(url, retryOptions);
}
