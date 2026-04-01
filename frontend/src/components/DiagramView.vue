<script setup>
import { computed, getCurrentInstance } from 'vue'

const props = defineProps({
  type: {
    type: String,
    default: 'plan'
  },
  la: {
    type: Number,
    default: 1.5
  },
  lb: {
    type: Number,
    default: 0.9
  },
  h: {
    type: Number,
    default: 2.0
  },
  hs: {
    type: Number,
    default: 22.7
  },
  wallGap: {
    type: Number,
    default: 0.3
  },
  diagonalBrace: {
    type: String,
    default: '每隔3跨一设'
  },
  tieMemberLayout: {
    type: String,
    default: 'ONE_STEP_TWO_SPAN'
  }
})

const pxPerMeter = 100
const tieLayoutLabelMap = {
  ONE_STEP_TWO_SPAN: '一步两跨',
  TWO_STEP_TWO_SPAN: '两步两跨',
  TWO_STEP_THREE_SPAN: '两步三跨'
}
const braceIntervalMap = {
  每隔1跨一设: 1,
  隔1布1: 1,
  每隔2跨一设: 3,
  隔2布1: 3,
  每隔3跨一设: 4,
  隔3布1: 4,
  每隔4跨一设: 5,
  隔4布1: 5
}
const tieSpanIntervalMap = {
  ONE_STEP_TWO_SPAN: 2,
  TWO_STEP_TWO_SPAN: 2,
  TWO_STEP_THREE_SPAN: 3
}

const instance = getCurrentInstance()
const instanceId = instance?.uid ?? 'diagram'

function toMetric(value, fallback = 0) {
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) {
    return fallback
  }
  return Math.max(numeric, 0)
}

function toPx(value) {
  return toMetric(value) * pxPerMeter
}

function toMmLabel(value, prefix = '') {
  const label = `${Math.round(toMetric(value) * 1000)}`
  return prefix ? `${prefix}=${label}` : label
}

function pointsToString(points) {
  return points.map(([x, y]) => `${x},${y}`).join(' ')
}

function createHorizontalBreakLine(x1, x2, y, direction) {
  const mid = (x1 + x2) / 2
  const peakY = direction === 'up' ? y - 14 : y + 14
  return pointsToString([
    [x1, y],
    [x1 + 40, y],
    [mid, peakY],
    [mid + 20, y],
    [x2, y]
  ])
}

function createVerticalBreakLine(x, y1, y2) {
  const midY = (y1 + y2) / 2
  return pointsToString([
    [x, y1],
    [x, midY - 10],
    [x + 14, midY],
    [x, midY + 10],
    [x, y2]
  ])
}

const wallPatternId = computed(() => `wall-hatch-${instanceId}-${props.type}`)
const tieLayoutLabel = computed(() => tieLayoutLabelMap[props.tieMemberLayout] || props.tieMemberLayout || '一步两跨')

const sectionData = computed(() => {
  const wallFaceX = 50
  const wallGapPx = toPx(props.wallGap)
  const lbPx = toPx(props.lb)
  const hPx = toPx(props.h)
  const innerX = wallFaceX + wallGapPx
  const outerX = innerX + lbPx
  const nodeYs = [70, 70 + hPx, 70 + hPx * 2]
  const breakTopY = nodeYs[0] - 30
  const breakBotY = nodeYs[2] + 30
  const breakX1 = innerX - 24
  const breakX2 = outerX + 24
  const tieY = nodeYs[0] + hPx / 2
  const bottomDimY = breakBotY + 28
  const wallGapDimY = breakBotY + 54
  const stepDimX = outerX + 34
  const heightDimX = outerX + 72
  const labelX = outerX + 44
  const labelY = tieY - 16

  return {
    viewBox: `0 0 ${Math.max(outerX + 150, 320)} ${breakBotY + 80}`,
    wallRect: {
      x: 10,
      y: breakTopY - 18,
      width: wallFaceX - 10,
      height: breakBotY - breakTopY + 36
    },
    wallFaceX,
    breakTopY,
    breakBotY,
    breakTopPoints: createHorizontalBreakLine(breakX1, breakX2, breakTopY, 'up'),
    breakBottomPoints: createHorizontalBreakLine(breakX1, breakX2, breakBotY, 'down'),
    poles: [
      { key: 'inner', x: innerX },
      { key: 'outer', x: outerX }
    ],
    nodeBlocks: [
      ...nodeYs.map((y, index) => ({
        key: `inner-${index}`,
        x: innerX - 9,
        y: y - 5,
        width: 18,
        height: 10
      })),
      ...nodeYs.map((y, index) => ({
        key: `outer-${index}`,
        x: outerX - 9,
        y: y - 5,
        width: 18,
        height: 10
      }))
    ],
    ledgers: nodeYs.map((y, index) => ({
      key: index,
      x: innerX + 3,
      y: y - 4,
      width: Math.max(outerX - innerX - 6, 0),
      height: 8
    })),
    tieMember: {
      y: tieY,
      anchor: {
        x: wallFaceX - 6,
        y: tieY - 7,
        width: 10,
        height: 14
      },
      rodX1: wallFaceX,
      rodX2: outerX + 3,
      clamps: [
        { key: 'inner', x: innerX - 9, y: tieY - 7, width: 18, height: 14 },
        { key: 'outer', x: outerX - 9, y: tieY - 7, width: 18, height: 14 }
      ],
      label: {
        textX: labelX,
        textY: labelY,
        linePoints: pointsToString([
          [outerX + 12, tieY],
          [outerX + 28, tieY],
          [labelX - 8, labelY + 4]
        ])
      }
    },
    hDimension: {
      x: stepDimX,
      y1: nodeYs[0],
      y2: nodeYs[1],
      labelX: stepDimX + 8,
      labelY: (nodeYs[0] + nodeYs[1]) / 2 + 4,
      text: toMmLabel(props.h, 'h')
    },
    hsDimension: {
      x: heightDimX,
      y1: breakTopY,
      y2: breakBotY,
      labelX: heightDimX + 8,
      labelY: (breakTopY + breakBotY) / 2 + 4,
      text: toMmLabel(props.hs, 'hs')
    },
    lbDimension: {
      x1: innerX,
      x2: outerX,
      y: bottomDimY,
      labelX: (innerX + outerX) / 2,
      labelY: bottomDimY - 6,
      text: toMmLabel(props.lb, 'lb')
    },
    wallGapDimension: {
      x1: wallFaceX,
      x2: innerX,
      y: wallGapDimY,
      labelX: (wallFaceX + innerX) / 2,
      labelY: wallGapDimY - 6,
      text: toMmLabel(props.wallGap)
    }
  }
})

const elevationData = computed(() => {
  const displaySpans = 6
  const displaySteps = 4
  const spanPx = toPx(props.la)
  const stepPx = toPx(props.h)
  const startX = 60
  const startY = 60
  const poleXs = Array.from({ length: displaySpans + 1 }, (_, index) => startX + index * spanPx)
  const levelYs = Array.from({ length: displaySteps + 1 }, (_, index) => startY + index * stepPx)
  const breakTopY = startY - 20
  const breakBotY = startY + displaySteps * stepPx + 20
  const lastPoleX = poleXs[poleXs.length - 1]
  const braceInterval = braceIntervalMap[props.diagonalBrace] || 4
  const braceSpans = []

  for (let index = 0; index < displaySpans; index += 1) {
    if (index % braceInterval === 0) {
      braceSpans.push(index)
    }
  }

  const braces = braceSpans.flatMap((spanIndex) =>
    Array.from({ length: displaySteps }, (_, levelIndex) => ({
      key: `${spanIndex}-${levelIndex}`,
      x1: poleXs[spanIndex],
      y1: levelYs[levelIndex + 1],
      x2: poleXs[spanIndex + 1],
      y2: levelYs[levelIndex]
    }))
  )

  return {
    viewBox: `0 0 ${startX + displaySpans * spanPx + 120} ${breakBotY + 60}`,
    breakTopPoints: createHorizontalBreakLine(startX - 24, lastPoleX + 24, breakTopY, 'up'),
    breakBottomPoints: createHorizontalBreakLine(startX - 24, lastPoleX + 24, breakBotY, 'down'),
    breakTopY,
    breakBotY,
    poles: poleXs.map((x, index) => ({ key: index, x })),
    levels: levelYs.map((y, index) => ({ key: index, y })),
    nodes: poleXs.flatMap((x, xIndex) =>
      levelYs.map((y, yIndex) => ({
        key: `${xIndex}-${yIndex}`,
        x: x - 6,
        y: y - 6,
        width: 12,
        height: 12
      }))
    ),
    braces,
    hDimension: {
      x: lastPoleX + 36,
      y1: levelYs[0],
      y2: levelYs[1],
      labelX: lastPoleX + 44,
      labelY: (levelYs[0] + levelYs[1]) / 2 + 4,
      text: toMmLabel(props.h, 'h')
    },
    laDimension: {
      x1: poleXs[0],
      x2: poleXs[1],
      y: breakBotY + 28,
      labelX: (poleXs[0] + poleXs[1]) / 2,
      labelY: breakBotY + 22,
      text: toMmLabel(props.la, 'la')
    }
  }
})

const planData = computed(() => {
  const displaySpans = 3
  const spanPx = toPx(props.la)
  const lbPx = toPx(props.lb)
  const wallGapPx = toPx(props.wallGap)
  const wallFaceY = 56
  const innerY = wallFaceY + wallGapPx
  const outerY = innerY + lbPx
  const poleStartX = 60
  const poleXs = Array.from({ length: displaySpans + 1 }, (_, index) => poleStartX + index * spanPx)
  const lastPoleX = poleXs[poleXs.length - 1]
  const breakX = lastPoleX + 30
  const tieInterval = tieSpanIntervalMap[props.tieMemberLayout] || 2
  const tieMemberXs = []

  for (let index = 0; index < displaySpans; index += 1) {
    if (index % tieInterval === 0) {
      tieMemberXs.push(poleXs[index] + spanPx / 2)
    }
  }

  const calloutX = (tieMemberXs[0] ?? poleXs[1]) + 18
  const calloutY = wallFaceY - 16

  return {
    viewBox: `0 0 ${lastPoleX + 200} ${outerY + 80}`,
    wallRect: {
      x: 18,
      y: 18,
      width: lastPoleX + spanPx / 2 - 18,
      height: wallFaceY - 18
    },
    wallFaceY,
    breakX,
    breakPoints: createVerticalBreakLine(breakX, 18, outerY + 30),
    poleXs,
    longitudinalRods: [
      { key: 'inner-top', y: innerY - 3 },
      { key: 'inner-bottom', y: innerY + 3 },
      { key: 'outer-top', y: outerY - 3 },
      { key: 'outer-bottom', y: outerY + 3 }
    ],
    poles: [
      ...poleXs.map((x, index) => ({
        key: `inner-${index}`,
        x: x - 6,
        y: innerY - 6,
        width: 12,
        height: 12
      })),
      ...poleXs.map((x, index) => ({
        key: `outer-${index}`,
        x: x - 6,
        y: outerY - 6,
        width: 12,
        height: 12
      }))
    ],
    crossLedgers: poleXs.map((x, index) => ({
      key: index,
      x1: x,
      y1: innerY + 6,
      x2: x,
      y2: outerY - 6
    })),
    tieMembers: tieMemberXs.map((x, index) => ({
      key: index,
      x,
      anchor: {
        x: x - 7,
        y: wallFaceY - 6,
        width: 14,
        height: 12
      }
    })),
    callout: {
      text: `连墙件（${tieLayoutLabel.value}）`,
      textX: calloutX,
      textY: calloutY,
      linePoints: pointsToString([
        [calloutX - 8, calloutY + 4],
        [calloutX - 20, calloutY + 4],
        [tieMemberXs[0] ?? poleXs[1], wallFaceY + 10]
      ])
    },
    laDimension: {
      x1: poleXs[0],
      x2: poleXs[1],
      y: outerY + 28,
      labelX: (poleXs[0] + poleXs[1]) / 2,
      labelY: outerY + 22,
      text: toMmLabel(props.la, 'la')
    },
    lbDimension: {
      x: breakX + 24,
      y1: innerY,
      y2: outerY,
      labelX: breakX + 32,
      labelY: (innerY + outerY) / 2 + 4,
      text: toMmLabel(props.lb, 'lb')
    },
    wallGapDimension: {
      x: breakX + 48,
      y1: wallFaceY,
      y2: innerY,
      labelX: breakX + 56,
      labelY: (wallFaceY + innerY) / 2 + 4,
      text: toMmLabel(props.wallGap)
    }
  }
})
</script>

<template>
  <svg
    v-if="type === 'section'"
    class="diagram-svg"
    width="100%"
    height="100%"
    :viewBox="sectionData.viewBox"
    preserveAspectRatio="xMidYMid meet"
  >
    <defs>
      <pattern :id="wallPatternId" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
        <line x1="0" y1="0" x2="0" y2="8" stroke="#d2d2d2" stroke-width="2" />
      </pattern>
    </defs>

    <rect
      :x="sectionData.wallRect.x"
      :y="sectionData.wallRect.y"
      :width="sectionData.wallRect.width"
      :height="sectionData.wallRect.height"
      :fill="`url(#${wallPatternId})`"
      stroke="#bcbcbc"
      stroke-width="1"
    />
    <line
      :x1="sectionData.wallFaceX"
      :x2="sectionData.wallFaceX"
      :y1="sectionData.breakTopY - 6"
      :y2="sectionData.breakBotY + 6"
      stroke="#7f7f7f"
      stroke-width="1.5"
      stroke-dasharray="5 4"
    />
    <polyline
      :points="sectionData.breakTopPoints"
      fill="none"
      stroke="#222222"
      stroke-width="2.2"
      stroke-linejoin="round"
    />
    <polyline
      :points="sectionData.breakBottomPoints"
      fill="none"
      stroke="#222222"
      stroke-width="2.2"
      stroke-linejoin="round"
    />
    <template v-for="pole in sectionData.poles" :key="pole.key">
      <line
        :x1="pole.x - 3"
        :x2="pole.x - 3"
        :y1="sectionData.breakTopY"
        :y2="sectionData.breakBotY"
        stroke="#222222"
        stroke-width="2"
      />
      <line
        :x1="pole.x + 3"
        :x2="pole.x + 3"
        :y1="sectionData.breakTopY"
        :y2="sectionData.breakBotY"
        stroke="#222222"
        stroke-width="2"
      />
    </template>
    <rect
      v-for="node in sectionData.nodeBlocks"
      :key="node.key"
      :x="node.x"
      :y="node.y"
      :width="node.width"
      :height="node.height"
      rx="1.5"
      fill="#444444"
    />
    <rect
      v-for="ledger in sectionData.ledgers"
      :key="ledger.key"
      :x="ledger.x"
      :y="ledger.y"
      :width="ledger.width"
      :height="ledger.height"
      rx="2"
      fill="#4a8fc1"
    />
    <rect
      :x="sectionData.tieMember.anchor.x"
      :y="sectionData.tieMember.anchor.y"
      :width="sectionData.tieMember.anchor.width"
      :height="sectionData.tieMember.anchor.height"
      fill="#cc2222"
      rx="1.5"
    />
    <line
      :x1="sectionData.tieMember.rodX1"
      :x2="sectionData.tieMember.rodX2"
      :y1="sectionData.tieMember.y"
      :y2="sectionData.tieMember.y"
      stroke="#cc2222"
      stroke-width="2.5"
    />
    <rect
      v-for="clamp in sectionData.tieMember.clamps"
      :key="clamp.key"
      :x="clamp.x"
      :y="clamp.y"
      :width="clamp.width"
      :height="clamp.height"
      fill="none"
      stroke="#cc2222"
      stroke-width="2"
      rx="2"
    />
    <polyline
      :points="sectionData.tieMember.label.linePoints"
      fill="none"
      stroke="#cc2222"
      stroke-width="1.8"
      stroke-linecap="round"
      stroke-linejoin="round"
    />
    <text
      :x="sectionData.tieMember.label.textX"
      :y="sectionData.tieMember.label.textY"
      fill="#cc2222"
      font-size="12"
      font-weight="600"
    >
      连墙件
    </text>

    <line
      :x1="sectionData.hDimension.x"
      :x2="sectionData.hDimension.x"
      :y1="sectionData.hDimension.y1"
      :y2="sectionData.hDimension.y2"
      stroke="#666666"
      stroke-width="1.4"
    />
    <line
      :x1="sectionData.hDimension.x - 5"
      :x2="sectionData.hDimension.x + 5"
      :y1="sectionData.hDimension.y1"
      :y2="sectionData.hDimension.y1"
      stroke="#666666"
      stroke-width="1.4"
    />
    <line
      :x1="sectionData.hDimension.x - 5"
      :x2="sectionData.hDimension.x + 5"
      :y1="sectionData.hDimension.y2"
      :y2="sectionData.hDimension.y2"
      stroke="#666666"
      stroke-width="1.4"
    />
    <text
      :x="sectionData.hDimension.labelX"
      :y="sectionData.hDimension.labelY"
      fill="#444444"
      font-size="11"
    >
      {{ sectionData.hDimension.text }}
    </text>

    <line
      :x1="sectionData.hsDimension.x"
      :x2="sectionData.hsDimension.x"
      :y1="sectionData.hsDimension.y1"
      :y2="sectionData.hsDimension.y2"
      stroke="#666666"
      stroke-width="1.4"
    />
    <line
      :x1="sectionData.hsDimension.x - 5"
      :x2="sectionData.hsDimension.x + 5"
      :y1="sectionData.hsDimension.y1"
      :y2="sectionData.hsDimension.y1"
      stroke="#666666"
      stroke-width="1.4"
    />
    <line
      :x1="sectionData.hsDimension.x - 5"
      :x2="sectionData.hsDimension.x + 5"
      :y1="sectionData.hsDimension.y2"
      :y2="sectionData.hsDimension.y2"
      stroke="#666666"
      stroke-width="1.4"
    />
    <text
      :x="sectionData.hsDimension.labelX"
      :y="sectionData.hsDimension.labelY"
      fill="#444444"
      font-size="11"
    >
      {{ sectionData.hsDimension.text }}
    </text>

    <line
      :x1="sectionData.lbDimension.x1"
      :x2="sectionData.lbDimension.x2"
      :y1="sectionData.lbDimension.y"
      :y2="sectionData.lbDimension.y"
      stroke="#666666"
      stroke-width="1.4"
    />
    <line
      :x1="sectionData.lbDimension.x1"
      :x2="sectionData.lbDimension.x1"
      :y1="sectionData.lbDimension.y - 5"
      :y2="sectionData.lbDimension.y + 5"
      stroke="#666666"
      stroke-width="1.4"
    />
    <line
      :x1="sectionData.lbDimension.x2"
      :x2="sectionData.lbDimension.x2"
      :y1="sectionData.lbDimension.y - 5"
      :y2="sectionData.lbDimension.y + 5"
      stroke="#666666"
      stroke-width="1.4"
    />
    <text
      :x="sectionData.lbDimension.labelX"
      :y="sectionData.lbDimension.labelY"
      fill="#444444"
      font-size="11"
      text-anchor="middle"
    >
      {{ sectionData.lbDimension.text }}
    </text>

    <line
      :x1="sectionData.wallGapDimension.x1"
      :x2="sectionData.wallGapDimension.x2"
      :y1="sectionData.wallGapDimension.y"
      :y2="sectionData.wallGapDimension.y"
      stroke="#666666"
      stroke-width="1.4"
    />
    <line
      :x1="sectionData.wallGapDimension.x1"
      :x2="sectionData.wallGapDimension.x1"
      :y1="sectionData.wallGapDimension.y - 5"
      :y2="sectionData.wallGapDimension.y + 5"
      stroke="#666666"
      stroke-width="1.4"
    />
    <line
      :x1="sectionData.wallGapDimension.x2"
      :x2="sectionData.wallGapDimension.x2"
      :y1="sectionData.wallGapDimension.y - 5"
      :y2="sectionData.wallGapDimension.y + 5"
      stroke="#666666"
      stroke-width="1.4"
    />
    <text
      :x="sectionData.wallGapDimension.labelX"
      :y="sectionData.wallGapDimension.labelY"
      fill="#444444"
      font-size="11"
      text-anchor="middle"
    >
      {{ sectionData.wallGapDimension.text }}
    </text>
  </svg>

  <svg
    v-else-if="type === 'elevation'"
    class="diagram-svg"
    width="100%"
    height="100%"
    :viewBox="elevationData.viewBox"
    preserveAspectRatio="xMidYMid meet"
  >
    <polyline
      :points="elevationData.breakTopPoints"
      fill="none"
      stroke="#222222"
      stroke-width="2.2"
      stroke-linejoin="round"
    />
    <polyline
      :points="elevationData.breakBottomPoints"
      fill="none"
      stroke="#222222"
      stroke-width="2.2"
      stroke-linejoin="round"
    />
    <line
      v-for="pole in elevationData.poles"
      :key="`pole-${pole.key}`"
      :x1="pole.x"
      :x2="pole.x"
      :y1="elevationData.breakTopY"
      :y2="elevationData.breakBotY"
      stroke="#222222"
      stroke-width="2.5"
    />
    <line
      v-for="level in elevationData.levels"
      :key="`level-${level.key}`"
      :x1="elevationData.poles[0].x"
      :x2="elevationData.poles[elevationData.poles.length - 1].x"
      :y1="level.y"
      :y2="level.y"
      stroke="#888888"
      stroke-width="1"
    />
    <line
      v-for="brace in elevationData.braces"
      :key="brace.key"
      :x1="brace.x1"
      :x2="brace.x2"
      :y1="brace.y1"
      :y2="brace.y2"
      stroke="#cc2222"
      stroke-width="2"
      stroke-linecap="round"
    />
    <rect
      v-for="node in elevationData.nodes"
      :key="node.key"
      :x="node.x"
      :y="node.y"
      :width="node.width"
      :height="node.height"
      fill="#444444"
      rx="1.5"
    />

    <line
      :x1="elevationData.hDimension.x"
      :x2="elevationData.hDimension.x"
      :y1="elevationData.hDimension.y1"
      :y2="elevationData.hDimension.y2"
      stroke="#666666"
      stroke-width="1.4"
    />
    <line
      :x1="elevationData.hDimension.x - 5"
      :x2="elevationData.hDimension.x + 5"
      :y1="elevationData.hDimension.y1"
      :y2="elevationData.hDimension.y1"
      stroke="#666666"
      stroke-width="1.4"
    />
    <line
      :x1="elevationData.hDimension.x - 5"
      :x2="elevationData.hDimension.x + 5"
      :y1="elevationData.hDimension.y2"
      :y2="elevationData.hDimension.y2"
      stroke="#666666"
      stroke-width="1.4"
    />
    <text
      :x="elevationData.hDimension.labelX"
      :y="elevationData.hDimension.labelY"
      fill="#444444"
      font-size="11"
    >
      {{ elevationData.hDimension.text }}
    </text>

    <line
      :x1="elevationData.laDimension.x1"
      :x2="elevationData.laDimension.x2"
      :y1="elevationData.laDimension.y"
      :y2="elevationData.laDimension.y"
      stroke="#666666"
      stroke-width="1.4"
    />
    <line
      :x1="elevationData.laDimension.x1"
      :x2="elevationData.laDimension.x1"
      :y1="elevationData.laDimension.y - 5"
      :y2="elevationData.laDimension.y + 5"
      stroke="#666666"
      stroke-width="1.4"
    />
    <line
      :x1="elevationData.laDimension.x2"
      :x2="elevationData.laDimension.x2"
      :y1="elevationData.laDimension.y - 5"
      :y2="elevationData.laDimension.y + 5"
      stroke="#666666"
      stroke-width="1.4"
    />
    <text
      :x="elevationData.laDimension.labelX"
      :y="elevationData.laDimension.labelY"
      fill="#444444"
      font-size="11"
      text-anchor="middle"
    >
      {{ elevationData.laDimension.text }}
    </text>
  </svg>

  <svg
    v-else
    class="diagram-svg"
    width="100%"
    height="100%"
    :viewBox="planData.viewBox"
    preserveAspectRatio="xMidYMid meet"
  >
    <defs>
      <pattern :id="wallPatternId" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
        <line x1="0" y1="0" x2="0" y2="8" stroke="#d2d2d2" stroke-width="2" />
      </pattern>
    </defs>

    <rect
      :x="planData.wallRect.x"
      :y="planData.wallRect.y"
      :width="planData.wallRect.width"
      :height="planData.wallRect.height"
      :fill="`url(#${wallPatternId})`"
      stroke="#bcbcbc"
      stroke-width="1"
    />
    <line
      x1="18"
      :x2="planData.breakX"
      :y1="planData.wallFaceY"
      :y2="planData.wallFaceY"
      stroke="#7f7f7f"
      stroke-width="1.5"
      stroke-dasharray="5 4"
    />
    <polyline
      :points="planData.breakPoints"
      fill="none"
      stroke="#222222"
      stroke-width="2.2"
      stroke-linejoin="round"
    />
    <line
      v-for="rod in planData.longitudinalRods"
      :key="rod.key"
      x1="18"
      :x2="planData.breakX"
      :y1="rod.y"
      :y2="rod.y"
      stroke="#cc2222"
      stroke-width="2.2"
      stroke-linecap="round"
    />
    <line
      v-for="ledger in planData.crossLedgers"
      :key="ledger.key"
      :x1="ledger.x1"
      :x2="ledger.x2"
      :y1="ledger.y1"
      :y2="ledger.y2"
      stroke="#4a8fc1"
      stroke-width="3.5"
      stroke-linecap="round"
    />
    <rect
      v-for="pole in planData.poles"
      :key="pole.key"
      :x="pole.x"
      :y="pole.y"
      :width="pole.width"
      :height="pole.height"
      fill="#1a5fa8"
      rx="1.5"
    />
    <template v-for="tie in planData.tieMembers" :key="tie.key">
      <rect
        :x="tie.anchor.x"
        :y="tie.anchor.y"
        :width="tie.anchor.width"
        :height="tie.anchor.height"
        fill="#cc2222"
        rx="1.5"
      />
      <line
        :x1="tie.x"
        :x2="tie.x"
        :y1="planData.wallFaceY"
        :y2="planData.longitudinalRods[3].y"
        stroke="#cc2222"
        stroke-width="2.5"
      />
      <circle
        :cx="tie.x"
        :cy="planData.longitudinalRods[0].y + 3"
        r="7"
        fill="#ffffff"
        stroke="#cc2222"
        stroke-width="2"
      />
      <circle
        :cx="tie.x"
        :cy="planData.longitudinalRods[2].y + 3"
        r="7"
        fill="#ffffff"
        stroke="#cc2222"
        stroke-width="2"
      />
    </template>
    <polyline
      :points="planData.callout.linePoints"
      fill="none"
      stroke="#cc2222"
      stroke-width="1.8"
      stroke-linecap="round"
      stroke-linejoin="round"
    />
    <text
      :x="planData.callout.textX"
      :y="planData.callout.textY"
      fill="#cc2222"
      font-size="12"
      font-weight="600"
    >
      {{ planData.callout.text }}
    </text>

    <line
      :x1="planData.laDimension.x1"
      :x2="planData.laDimension.x2"
      :y1="planData.laDimension.y"
      :y2="planData.laDimension.y"
      stroke="#666666"
      stroke-width="1.4"
    />
    <line
      :x1="planData.laDimension.x1"
      :x2="planData.laDimension.x1"
      :y1="planData.laDimension.y - 5"
      :y2="planData.laDimension.y + 5"
      stroke="#666666"
      stroke-width="1.4"
    />
    <line
      :x1="planData.laDimension.x2"
      :x2="planData.laDimension.x2"
      :y1="planData.laDimension.y - 5"
      :y2="planData.laDimension.y + 5"
      stroke="#666666"
      stroke-width="1.4"
    />
    <text
      :x="planData.laDimension.labelX"
      :y="planData.laDimension.labelY"
      fill="#444444"
      font-size="11"
      text-anchor="middle"
    >
      {{ planData.laDimension.text }}
    </text>

    <line
      :x1="planData.lbDimension.x"
      :x2="planData.lbDimension.x"
      :y1="planData.lbDimension.y1"
      :y2="planData.lbDimension.y2"
      stroke="#666666"
      stroke-width="1.4"
    />
    <line
      :x1="planData.lbDimension.x - 5"
      :x2="planData.lbDimension.x + 5"
      :y1="planData.lbDimension.y1"
      :y2="planData.lbDimension.y1"
      stroke="#666666"
      stroke-width="1.4"
    />
    <line
      :x1="planData.lbDimension.x - 5"
      :x2="planData.lbDimension.x + 5"
      :y1="planData.lbDimension.y2"
      :y2="planData.lbDimension.y2"
      stroke="#666666"
      stroke-width="1.4"
    />
    <text
      :x="planData.lbDimension.labelX"
      :y="planData.lbDimension.labelY"
      fill="#444444"
      font-size="11"
    >
      {{ planData.lbDimension.text }}
    </text>

    <line
      :x1="planData.wallGapDimension.x"
      :x2="planData.wallGapDimension.x"
      :y1="planData.wallGapDimension.y1"
      :y2="planData.wallGapDimension.y2"
      stroke="#666666"
      stroke-width="1.4"
    />
    <line
      :x1="planData.wallGapDimension.x - 5"
      :x2="planData.wallGapDimension.x + 5"
      :y1="planData.wallGapDimension.y1"
      :y2="planData.wallGapDimension.y1"
      stroke="#666666"
      stroke-width="1.4"
    />
    <line
      :x1="planData.wallGapDimension.x - 5"
      :x2="planData.wallGapDimension.x + 5"
      :y1="planData.wallGapDimension.y2"
      :y2="planData.wallGapDimension.y2"
      stroke="#666666"
      stroke-width="1.4"
    />
    <text
      :x="planData.wallGapDimension.labelX"
      :y="planData.wallGapDimension.labelY"
      fill="#444444"
      font-size="11"
    >
      {{ planData.wallGapDimension.text }}
    </text>
  </svg>
</template>

<style scoped>
.diagram-svg {
  width: 100%;
  height: 100%;
  display: block;
}
</style>
