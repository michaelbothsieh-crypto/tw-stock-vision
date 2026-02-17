
precision highp float;

uniform float uTime;
uniform vec3 uColor;
uniform float uOpacity;
uniform float uBuoyancy;    // 浮力
uniform float uDiffusion;   // 擴散率
uniform float uVolatility;  // 波動度
varying vec2 vUv;

// Simplex 2D noise
vec3 permute(vec3 x) { return mod(((x*34.0)+1.0)*x, 289.0); }

float snoise(vec2 v){
  const vec4 C = vec4(0.211324865405187, 0.366025403784439,
           -0.577350269189626, 0.024390243902439);
  vec2 i  = floor(v + dot(v, C.yy) );
  vec2 x0 = v -   i + dot(i, C.xx);
  vec2 i1;
  i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
  vec4 x12 = x0.xyxy + C.xxzz;
  x12.xy -= i1;
  i = mod(i, 289.0);
  vec3 p = permute( permute( i.y + vec3(0.0, i1.y, 1.0 ))
  + i.x + vec3(0.0, i1.x, 1.0 ));
  vec3 m = max(0.5 - vec4(dot(x0,x0), dot(x12.xy,x12.xy),
    dot(x12.zw,x12.zw), 0.0), 0.0);
  m = m*m ;
  m = m*m ;
  vec3 x = 2.0 * fract(p * C.www) - 1.0;
  vec3 h = abs(x) - 0.5;
  vec3 a0 = x - floor(x + 0.5);
  vec3 g = a0 * vec3(x0.x,x12.xz) + h * vec3(x0.y,x12.yw);
  return 130.0 * dot(m, g);
}

void main() {
    vec2 uv = vUv;
    
    // 根據時間與浮力模擬升騰效果 (Ink rising)
    float motion = snoise(uv * 3.0 + vec2(0.0, uTime * uBuoyancy * 0.5));
    float alpha = smoothstep(0.5, 0.2, length(uv - 0.5));
    
    // 擴散效果
    alpha *= (1.0 - uDiffusion * 0.5);
    
    // 顏色與輝度
    vec3 color = uColor + motion * uVolatility * 0.2;
    
    // 邊緣軟化
    float dist = distance(uv, vec2(0.5));
    float edge = 1.0 - smoothstep(0.4, 0.5, dist);
    
    gl_FragColor = vec4(color, uOpacity * alpha * edge);
}
