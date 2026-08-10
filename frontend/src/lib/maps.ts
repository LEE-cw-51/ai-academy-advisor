/**
 * 네이버 지도 길찾기 URL.
 * 형식: /p/directions/{출발}/{도착}/{경유}/{수단} — 출발지는 "-"로 두면
 * 네이버가 사용자의 현재 위치를 출발지로 잡는다.
 */
export function naverDirectionsUrl(
  latitude: number,
  longitude: number,
  name: string,
): string {
  const goal = `${longitude},${latitude},${encodeURIComponent(name)}`;
  return `https://map.naver.com/p/directions/-/${goal}/-/transit`;
}
