"use client";

import React, { useEffect, useRef, useMemo } from "react";
import { cn } from "@/lib/utils";

export interface AgenticBallProps {
  size?: number;
  width?: string | number;
  height?: string | number;
  className?: string;
  children?: React.ReactNode;
  speed?: number;
  complexity?: number;
  swirl?: number;
  zoom?: number;
  color?: string;
  hueRotation?: number;
  saturation?: number;
  brightness?: number;
  backgroundColor?: string;
  opacity?: number;
}

function hexToRgb(hex: string): [number, number, number] {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result
    ? [
        parseInt(result[1], 16) / 255,
        parseInt(result[2], 16) / 255,
        parseInt(result[3], 16) / 255,
      ]
    : [0, 0, 0];
}

const VERTEX_SHADER_SRC = `
attribute vec2 position;
varying vec2 vUv;
void main() {
  vUv = (position + 1.0) * 0.5;
  gl_Position = vec4(position, 0.0, 1.0);
}
`;

const FRAGMENT_SHADER_SRC = `
#ifdef GL_ES
#ifdef GL_FRAGMENT_PRECISION_HIGH
precision highp float;
#else
precision mediump float;
#endif
#endif

#extension GL_OES_standard_derivatives : enable

uniform float uTime;
uniform vec2  uRes;
uniform float uSpeed;
uniform float uComplexity;
uniform float uSwirl;
uniform float uZoom;
uniform vec3  uTint;
uniform float uHueRotation;
uniform float uSaturation;
uniform float uBrightness;
uniform vec3  uBg;
uniform float uAlpha;

varying vec2 vUv;

vec2 spin(vec2 v, float a) {
  return cos(a) * v + sin(a) * vec2(-v.y, v.x);
}

float sfrac(float x, float k) {
  float f = fract(x);
  return f * smoothstep(1.0, k, f);
}

vec3 hueRotate(vec3 col, float angle) {
  return mix(vec3(dot(vec3(0.33333333), col)), col, cos(angle))
       + cross(vec3(0.57735027), col) * sin(angle);
}

vec3 computeOrb(vec3 p, float t) {
  vec3 v = vec3(0.0);
  float x = 0.0;
  float y = 0.0;
  float it = uComplexity;
  float halo = smoothstep(0.5, 0.0, p.z);
  vec3 c = vec3(0.0);

  for (float i = 1.0; i < 9.0; i += 1.0) {
    if (i > it) break;

    p.xy = spin(p.xy, p.z * uSwirl + t / i * 0.4);
    v = v * 0.5 + 0.5;
    v.xz = spin(v.xz, v.y - x + t / i + p.y);
    p.xy = spin(p.xy, length(v.xy) - x);

    x += sfrac(v.z, 0.9 - sin(y * 1.5) * 0.2 + p.z * 0.1) / it / (1.0 + x + x * x);
    y += sfrac(-v.z, 0.9 + sin(x) * 0.1) / it;

    c += exp(vec3(0.7, 1.9, 4.0) * log(max(x, 1e-8)));
  }

  float xy = (x - y) * (x - y);
  c += xy * sqrt(max(c, 0.0));
  c = clamp(c, 0.0, 1.0);

  c = hueRotate(c, uHueRotation);

  c = mix(vec3(dot(c, vec3(0.2, 0.7, 0.1))), c, uSaturation * (1.0 + y));
  c = max(c, 0.0);

  float bgLum = dot(uBg, vec3(0.2, 0.7, 0.1));
  float rimLift = bgLum * 0.5;
  c = mix(c, sqrt(max(c, 0.0)) * 0.7 + rimLift * 0.6, halo);
  c = mix(c, sqrt(max(c, 0.0)) * 0.5 + rimLift, sqrt(halo));

  c *= uTint;

  return c;
}

void main() {
  vec4 bg = vec4(uBg, uAlpha);
  vec2 uv = (gl_FragCoord.xy * 2.0 - uRes) / min(uRes.x, uRes.y) * uZoom;
  float t = uTime * uSpeed;

  float l2 = dot(uv, uv);
  float l = sqrt(l2);

  if (l > 1.0) {
    gl_FragColor = bg;
    return;
  }

  vec3 sn = vec3(uv, sqrt(1.0 - l2));
  vec3 n = computeOrb(sn, t) * uBrightness;

  float edge = 1.0;
  #ifdef GL_OES_standard_derivatives
  float f = length(vec2(dFdx(l), dFdy(l)));
  edge = smoothstep(1.0 - f, 1.0 - f * 3.0, l);
  #else
  float f = 0.005;
  edge = smoothstep(1.0 - f, 1.0 - f * 3.0, l);
  #endif

  gl_FragColor = mix(bg, vec4(sqrt(max(n, 0.0)), uAlpha), edge);
}
`;

/**
 * AgenticBall - Animated 3D orb with swirl and glow effects from React Bits Pro
 */
export default function AgenticBall({
  size,
  width = size ?? "100%",
  height = size ?? "100%",
  className,
  children,
  speed = 0.5,
  complexity = 3,
  swirl = 2.0,
  zoom = 1.75,
  color = "#FFFFFF",
  hueRotation = 4.3,
  saturation = 0,
  brightness = 2,
  backgroundColor = "#000000",
  opacity = 1,
}: AgenticBallProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const tintRgb = useMemo(() => hexToRgb(color), [color]);
  const bgRgb = useMemo(() => hexToRgb(backgroundColor), [backgroundColor]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    let gl = canvas.getContext("webgl2") as WebGLRenderingContext | null;
    if (!gl) {
      gl = (canvas.getContext("webgl") ||
        canvas.getContext("experimental-webgl")) as WebGLRenderingContext | null;
      if (gl) {
        gl.getExtension("OES_standard_derivatives");
      }
    }

    if (!gl) return;

    // Compile vertex shader
    const vs = gl.createShader(gl.VERTEX_SHADER);
    if (!vs) return;
    gl.shaderSource(vs, VERTEX_SHADER_SRC);
    gl.compileShader(vs);

    // Compile fragment shader
    const fs = gl.createShader(gl.FRAGMENT_SHADER);
    if (!fs) return;
    gl.shaderSource(fs, FRAGMENT_SHADER_SRC);
    gl.compileShader(fs);

    const program = gl.createProgram();
    if (!program) return;
    gl.attachShader(program, vs);
    gl.attachShader(program, fs);
    gl.linkProgram(program);

    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      console.warn("Shader program link error:", gl.getProgramInfoLog(program));
      return;
    }

    gl.useProgram(program);

    // Quad geometry covering screen [-1, 1]
    const quadVertices = new Float32Array([
      -1, -1,
       1, -1,
      -1,  1,
      -1,  1,
       1, -1,
       1,  1,
    ]);

    const vbo = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, vbo);
    gl.bufferData(gl.ARRAY_BUFFER, quadVertices, gl.STATIC_DRAW);

    const posLoc = gl.getAttribLocation(program, "position");
    gl.enableVertexAttribArray(posLoc);
    gl.vertexAttribPointer(posLoc, 2, gl.FLOAT, false, 0, 0);

    // Uniform locations
    const uTimeLoc = gl.getUniformLocation(program, "uTime");
    const uResLoc = gl.getUniformLocation(program, "uRes");
    const uSpeedLoc = gl.getUniformLocation(program, "uSpeed");
    const uComplexityLoc = gl.getUniformLocation(program, "uComplexity");
    const uSwirlLoc = gl.getUniformLocation(program, "uSwirl");
    const uZoomLoc = gl.getUniformLocation(program, "uZoom");
    const uTintLoc = gl.getUniformLocation(program, "uTint");
    const uHueRotationLoc = gl.getUniformLocation(program, "uHueRotation");
    const uSaturationLoc = gl.getUniformLocation(program, "uSaturation");
    const uBrightnessLoc = gl.getUniformLocation(program, "uBrightness");
    const uBgLoc = gl.getUniformLocation(program, "uBg");
    const uAlphaLoc = gl.getUniformLocation(program, "uAlpha");

    let animationFrameId: number;
    let startTime = performance.now();

    const resize = () => {
      if (!canvas) return;
      const rect = canvas.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const displayWidth = Math.round(rect.width * dpr);
      const displayHeight = Math.round(rect.height * dpr);

      if (canvas.width !== displayWidth || canvas.height !== displayHeight) {
        canvas.width = displayWidth;
        canvas.height = displayHeight;
      }
      if (gl) {
        gl.viewport(0, 0, canvas.width, canvas.height);
      }
    };

    resize();

    const render = (time: number) => {
      if (!gl || !canvas) return;
      resize();

      const elapsed = (time - startTime) * 0.001;

      gl.useProgram(program);

      gl.uniform1f(uTimeLoc, elapsed);
      gl.uniform2f(uResLoc, canvas.width, canvas.height);
      gl.uniform1f(uSpeedLoc, speed);
      gl.uniform1f(uComplexityLoc, complexity);
      gl.uniform1f(uSwirlLoc, swirl);
      gl.uniform1f(uZoomLoc, zoom);
      gl.uniform3f(uTintLoc, tintRgb[0], tintRgb[1], tintRgb[2]);
      gl.uniform1f(uHueRotationLoc, hueRotation);
      gl.uniform1f(uSaturationLoc, saturation);
      gl.uniform1f(uBrightnessLoc, brightness);
      gl.uniform3f(uBgLoc, bgRgb[0], bgRgb[1], bgRgb[2]);
      gl.uniform1f(uAlphaLoc, opacity);

      gl.drawArrays(gl.TRIANGLES, 0, 6);

      animationFrameId = requestAnimationFrame(render);
    };

    animationFrameId = requestAnimationFrame(render);

    return () => {
      cancelAnimationFrame(animationFrameId);
      if (gl) {
        gl.deleteProgram(program);
        gl.deleteShader(vs);
        gl.deleteShader(fs);
        gl.deleteBuffer(vbo);
      }
    };
  }, [
    speed,
    complexity,
    swirl,
    zoom,
    tintRgb,
    hueRotation,
    saturation,
    brightness,
    bgRgb,
    opacity,
  ]);

  return (
    <div
      className={cn("relative overflow-hidden inline-flex items-center justify-center", className)}
      style={{
        width: typeof width === "number" ? `${width}px` : width,
        height: typeof height === "number" ? `${height}px` : height,
      }}
    >
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full block"
        style={{ pointerEvents: "none" }}
      />
      {children && (
        <div className="relative z-10 pointer-events-none">{children}</div>
      )}
    </div>
  );
}

AgenticBall.displayName = "AgenticBall";
