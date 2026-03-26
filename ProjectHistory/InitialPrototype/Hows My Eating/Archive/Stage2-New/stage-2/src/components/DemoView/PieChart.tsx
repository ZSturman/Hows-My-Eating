import React from 'react';
import * as d3 from 'd3';

type PieChartProps = {
  trianglesWithArea: TriangleWithArea[];
};

const PieChart: React.FC<PieChartProps> = ({ trianglesWithArea }) => {
  const width = 250;
  const height = 250;
  const radius = Math.min(width, height) / 2;

  // Compute pie data
  const areas = trianglesWithArea.map((triangle) => triangle.area);
  const pie = d3.pie<number>().sort(null);
  const arcGenerator = d3
    .arc<d3.PieArcDatum<number>>()
    .innerRadius(40)
    .outerRadius(radius - 10);

  const arcs = pie(areas);

  console.log(trianglesWithArea)



  return (
    <div style={{ display: 'flex', justifyContent: 'center', padding: '20px' }}>
      <svg width={width} height={height}>
        <g transform={`translate(${width / 2}, ${height / 2})`}>
          {arcs.map((arc, index) => (
            <path
              key={index}
              d={arcGenerator(arc) ?? ''}
              fill={trianglesWithArea[index].canvas.color.pointColor}
              stroke={trianglesWithArea[index].canvas.color.lineColor}
              strokeWidth="2"
              style={{ cursor: 'pointer' }}
              onMouseEnter={(e) => e.currentTarget.setAttribute('opacity', '0.8')}
              onMouseLeave={(e) => e.currentTarget.setAttribute('opacity', '1')}
            />
          ))}
        </g>
        {trianglesWithArea.map((triangle, index) => (
          <text
            key={`label-${index}`}
            x={20}
            y={20 + index * 20}
            fontSize="12"
            fill="#333"
            fontFamily="Arial, sans-serif"
          >
            Triangle {index + 1} Area: {triangle.area.toFixed(2)}
          </text>
        ))}
      </svg>
    </div>
  );
};

export default PieChart;