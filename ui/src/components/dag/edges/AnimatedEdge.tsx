import { BaseEdge, getBezierPath, type EdgeProps } from '@xyflow/react';

export type AnimatedEdgeData = {
  /** Mirrors the edge's `animated` flag so the path can style itself. */
  animated: boolean;
};

export type AnimatedFlowEdge = EdgeProps & { data?: AnimatedEdgeData };

/**
 * Bezier edge that draws a marching-dash path while either endpoint is
 * mutating. React Flow still receives `animated` on the edge itself (that is
 * what the library's own CSS animates); the class below keeps the effect when
 * a host page overrides the library stylesheet.
 */
export default function AnimatedEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  markerEnd,
  markerStart,
  style,
  data,
  label,
  labelStyle,
  labelShowBg,
  labelBgStyle,
  labelBgPadding,
  labelBgBorderRadius,
}: EdgeProps) {
  const [path, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const animated = data?.animated === true;

  return (
    <BaseEdge
      id={id}
      path={path}
      markerEnd={markerEnd}
      markerStart={markerStart}
      style={style}
      className={animated ? 'animated' : undefined}
      labelX={labelX}
      labelY={labelY}
      label={label}
      labelStyle={labelStyle}
      labelShowBg={labelShowBg}
      labelBgStyle={labelBgStyle}
      labelBgPadding={labelBgPadding}
      labelBgBorderRadius={labelBgBorderRadius}
    />
  );
}
