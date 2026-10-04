/**
 * A change token for an embedded file, built from the metadata the backend
 * already returns (`mtime` in milliseconds and `size`). It goes into a `?v=`
 * query and a React `key`, so a recompiled or re-rendered file is fetched again
 * instead of served from the browser cache. The file routes ignore `v`.
 */
export function cacheToken(info: { mtime?: number; size?: number }): string {
  const parts = [info.mtime, info.size].filter((part): part is number => typeof part === 'number');
  return parts.join('-');
}

export function withVersion(url: string, info: { mtime?: number; size?: number }): string {
  const token = cacheToken(info);
  if (!token) return url;
  return `${url}${url.includes('?') ? '&' : '?'}v=${token}`;
}
