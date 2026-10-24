"""Unit quaternion and gap-aware timestamp helpers for future calibrated IMUs.

Orientation math is exact up to floating-point tolerances; anatomical meaning
requires physical sensor-to-segment alignment and measurement validation.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import acos, cos, sin, sqrt, isfinite, degrees
from bisect import bisect_left


@dataclass(frozen=True)
class Quaternion:
    w: float
    x: float
    y: float
    z: float

    def __post_init__(self):
        values = (self.w, self.x, self.y, self.z)
        if not all(isfinite(v) for v in values):
            raise ValueError("Quaternion components must be finite")
        norm = sqrt(sum(v*v for v in values))
        if norm < 1e-12:
            raise ValueError("Zero quaternion cannot be normalized")
        for name, value in zip(("w","x","y","z"), values):
            object.__setattr__(self, name, value / norm)

    def conjugate(self):
        return Quaternion(self.w, -self.x, -self.y, -self.z)

    def multiply(self, other: "Quaternion") -> "Quaternion":
        a,b,c,d=self.w,self.x,self.y,self.z
        e,f,g,h=other.w,other.x,other.y,other.z
        return Quaternion(a*e-b*f-c*g-d*h, a*f+b*e+c*h-d*g,
                          a*g-b*h+c*e+d*f, a*h+b*g-c*f+d*e)

    @classmethod
    def axis_angle(cls, axis: tuple[float,float,float], angle_rad: float):
        length=sqrt(sum(x*x for x in axis))
        if length < 1e-12 or not isfinite(angle_rad):
            raise ValueError("Axis must be nonzero and angle finite")
        half=angle_rad/2
        return cls(cos(half),*(sin(half)*x/length for x in axis))

    def rotate(self, vector: tuple[float,float,float]):
        """Rotate a 3-vector with the unit quaternion, preserving magnitude."""
        if len(vector)!=3 or not all(isfinite(v) for v in vector):
            raise ValueError("Finite three-dimensional vector expected")
        x,y,z=vector
        u=(self.x,self.y,self.z)
        cross=(u[1]*z-u[2]*y, u[2]*x-u[0]*z, u[0]*y-u[1]*x)
        t=tuple(2*v for v in cross)
        c=(u[1]*t[2]-u[2]*t[1],u[2]*t[0]-u[0]*t[2],u[0]*t[1]-u[1]*t[0])
        return (x+self.w*t[0]+c[0],y+self.w*t[1]+c[1],z+self.w*t[2]+c[2])


def relative_head_torso(head_world: Quaternion, torso_world: Quaternion) -> Quaternion:
    """Orientation R_torso^T R_head, expressed in torso coordinates."""
    return torso_world.conjugate().multiply(head_world)


def relative_angle_deg(head_world: Quaternion, torso_world: Quaternion) -> float:
    q=relative_head_torso(head_world,torso_world)
    return degrees(2*acos(min(1.0,abs(q.w))))  # shortest relative angle 0..180


def relative_angular_velocity_torso_frame(head_world: Quaternion, torso_world: Quaternion,
                                            head_gyro_local, torso_gyro_local):
    """Rotate both gyro vectors into world frame, subtract, return to torso frame."""
    a=head_world.rotate(head_gyro_local)
    b=torso_world.rotate(torso_gyro_local)
    return torso_world.conjugate().rotate(tuple(x-y for x,y in zip(a,b)))


def interpolate_no_gaps(times: list[float], values: list[float], query_times: list[float],
                         max_bracket_gap_s: float = .02) -> list[float | None]:
    """Scalar interpolation for synchronized sensor series, suppressing long gaps.

    Caller must ensure common clock and matching sensor timestamps; no
    extrapolation, quaternion interpolation, or anti-alias filtering included.
    """
    if (len(times)!=len(values) or len(times)<2 or max_bracket_gap_s<=0 or
        not all(isfinite(t) for t in times+values+query_times) or
        any(b<=a for a,b in zip(times,times[1:]))):
        raise ValueError("Finite, equal-length, strictly increasing sensor samples required")
    answer=[]
    for t in query_times:
        j=bisect_left(times,t)
        if j<len(times) and times[j]==t:
            answer.append(values[j]);continue
        if j==0 or j==len(times) or times[j]-times[j-1]>max_bracket_gap_s:
            answer.append(None);continue
        f=(t-times[j-1])/(times[j]-times[j-1])
        answer.append(values[j-1]*(1-f)+values[j]*f)
    return answer
