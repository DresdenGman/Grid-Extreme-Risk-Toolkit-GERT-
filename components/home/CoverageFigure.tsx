import type { FigureView } from '@/lib/homepage/figure';
import styles from './home.module.css';

const INK = '#1C1B18';
const MUTED = '#5F5D58';
const SIGNAL = '#8F2A1B';
const HAIRLINE = '#C4C1BA';

export function CoverageFigure({
  figure,
  title,
  description,
  fonts,
}: {
  figure: FigureView;
  title: string;
  description: string;
  fonts: { sans: string; serif: string; mono: string };
}) {
  return (
    <>
      <div className={styles.desktop}>
        <div className={styles.plate}>
          <svg
            viewBox={`0 0 ${figure.width} ${figure.height}`}
            role="img"
            aria-labelledby="fig1-title fig1-desc"
            style={{ fontFamily: fonts.sans }}
          >
            <title id="fig1-title">{title}</title>
            <desc id="fig1-desc">{description}</desc>
            <rect x="0" y="0" width={figure.width} height={figure.height} fill="#FFFEFB" />
            <text x="24" y="36" fontFamily={fonts.serif} fontStyle="italic" fontSize="20" fill={INK}>
              Signed coverage error, empirical minus nominal
            </text>
            {figure.legend.map((item) => (
              <g key={item.label}>
                {item.kind === 'square' ? (
                  <rect x={item.x} y="24" width="10" height="10" fill={SIGNAL} />
                ) : (
                  <g>
                    <line x1={item.x} y1="18" x2={item.x} y2="40" stroke={INK} strokeWidth="1.2" />
                    <circle cx={item.x} cy="29" r="4.5" fill={INK} />
                  </g>
                )}
                <text x={item.labelX} y="33" fontSize="12" fill={INK}>
                  {item.label}
                </text>
              </g>
            ))}
            <line x1="24" y1="56" x2={figure.plotRight} y2="56" stroke={HAIRLINE} strokeWidth="1" />
            <rect
              x={figure.band.x}
              y={figure.band.y}
              width={figure.band.width}
              height={figure.band.height}
              fill="rgba(28,27,24,0.075)"
            />
            <line
              x1={figure.plotLeft}
              y1={figure.band.y}
              x2={figure.plotRight}
              y2={figure.band.y}
              stroke={HAIRLINE}
              strokeWidth="1"
            />
            <line
              x1={figure.plotLeft}
              y1={figure.band.y + figure.band.height}
              x2={figure.plotRight}
              y2={figure.band.y + figure.band.height}
              stroke={HAIRLINE}
              strokeWidth="1"
            />
            <line
              x1={figure.plotLeft}
              y1={figure.yZero}
              x2={figure.plotRight}
              y2={figure.yZero}
              stroke={INK}
              strokeWidth="1.5"
            />
            <line x1={figure.plotLeft} y1="108" x2={figure.plotLeft} y2="856" stroke={INK} strokeWidth="1" />
            {figure.ticks.map((tick) => (
              <g key={tick.label}>
                <line x1="102" y1={tick.y} x2={figure.plotLeft} y2={tick.y} stroke={INK} strokeWidth="1" />
                <text
                  x="96"
                  y={tick.textY}
                  textAnchor="end"
                  fontFamily={fonts.mono}
                  fontSize="11"
                  fill={tick.tone === 'muted' ? MUTED : INK}
                >
                  {tick.label}
                </text>
              </g>
            ))}
            <text
              transform={`rotate(-90 36 ${figure.yZero})`}
              x="36"
              y={figure.yZero}
              textAnchor="middle"
              fontSize="11"
              letterSpacing="0.14em"
              fill={MUTED}
            >
              EMPIRICAL − NOMINAL
            </text>
            {figure.dividers.map((x) => (
              <line key={x} x1={x} y1="108" x2={x} y2="856" stroke={HAIRLINE} strokeWidth="1" />
            ))}
            {figure.columns.map((column) => (
              <g key={column.label}>
                <text x={column.x} y="80" textAnchor="middle" fontSize="20" fontWeight="500" fill={INK}>
                  {column.label}
                </text>
                <text x={column.x} y="96" textAnchor="middle" fontFamily={fonts.mono} fontSize="11" fill={MUTED}>
                  {column.nominal}
                </text>
                {column.v14.stub ? (
                  <line
                    x1={column.v14.stub.x}
                    y1={column.v14.stub.y1}
                    x2={column.v14.stub.x}
                    y2={column.v14.stub.y2}
                    stroke={SIGNAL}
                    strokeWidth="1.35"
                  />
                ) : null}
                <rect
                  x={column.v14.square.x}
                  y={column.v14.square.y}
                  width={column.v14.square.size}
                  height={column.v14.square.size}
                  fill={SIGNAL}
                />
                <text textAnchor="end" fontFamily={fonts.mono} fill={SIGNAL}>
                  <tspan x={column.v14.labelX} y={column.v14.labelY} fontSize={column.v14.signedSize}>
                    {column.v14.signed}
                  </tspan>
                  <tspan x={column.v14.labelX} y={column.v14.labelY + 16} fontSize="10">
                    emp {column.v14.emp}
                  </tspan>
                </text>
                {column.v15 ? (
                  <g>
                    {column.v15.ci ? (
                      <g>
                        <line
                          x1={column.v15.x}
                          y1={column.v15.y1}
                          x2={column.v15.x}
                          y2={column.v15.y2}
                          stroke={INK}
                          strokeWidth="1.25"
                        />
                        <line
                          x1={column.v15.x - 5}
                          y1={column.v15.y1}
                          x2={column.v15.x + 5}
                          y2={column.v15.y1}
                          stroke={INK}
                          strokeWidth="1.25"
                        />
                        <line
                          x1={column.v15.x - 5}
                          y1={column.v15.y2}
                          x2={column.v15.x + 5}
                          y2={column.v15.y2}
                          stroke={INK}
                          strokeWidth="1.25"
                        />
                      </g>
                    ) : null}
                    <circle cx={column.v15.x} cy={column.v15.y} r="5.5" fill={INK} />
                    {column.v15.note ? (
                      <text
                        x={column.v15.note.x}
                        y={column.v15.note.y}
                        fontFamily={fonts.sans}
                        fontStyle="italic"
                        fontSize="10"
                        fill={MUTED}
                      >
                        {column.v15.note.text}
                      </text>
                    ) : null}
                    <text fontFamily={fonts.mono} fill={INK}>
                      <tspan x={column.v15.labelX} y={column.v15.labelY} fontSize="11">
                        {column.v15.signed}
                      </tspan>
                      <tspan x={column.v15.labelX} y={column.v15.labelY + 14} fontSize="10" fill={MUTED}>
                        emp {column.v15.emp}
                      </tspan>
                      {column.v15.ci ? (
                        <tspan x={column.v15.labelX} y={column.v15.labelY + 26} fontSize="10" fill={MUTED}>
                          CI {column.v15.ci}
                        </tspan>
                      ) : null}
                    </text>
                  </g>
                ) : null}
              </g>
            ))}
            <rect x={figure.plotLeft} y="872" width="16" height="10" fill="rgba(28,27,24,0.075)" stroke={HAIRLINE} strokeWidth="0.7" />
            <text x="132" y="881" fontSize="11" fill={MUTED}>
              {figure.axisNote}
            </text>
          </svg>
        </div>
      </div>

      <div className={styles.mobile}>
        <div className={styles.mobileLegend}>
          {figure.legend.map((item) => (
            <span key={item.label}>
              <span className={item.kind === 'square' ? styles.swatch : styles.swatchInterval} />
              {item.label}
            </span>
          ))}
        </div>
        {figure.mobile.rows.map((row) => (
          <article key={row.label} className={styles.mobileRow}>
            <header className={styles.mobileHead}>
              <span className={styles.mobileQ}>{row.label}</span>
              <span className={styles.mobileNominal}>nominal {row.nominal}</span>
            </header>
            <div className={styles.trackWrap}>
              <div className={styles.track}>
                <div
                  className={styles.band}
                  style={{ left: `${figure.mobile.bandLeft}%`, width: `${figure.mobile.bandWidth}%` }}
                />
                <div className={styles.zero} style={{ left: `${figure.mobile.zeroPct}%` }} />
                {row.v15 && row.v15.ci ? (
                  <div
                    className={styles.ci}
                    style={{ left: `${row.v15.ciLeft}%`, width: `${row.v15.ciWidth}%` }}
                  />
                ) : null}
                <div className={styles.sq} style={{ left: `${row.v14Pct}%` }} />
                {row.v15 ? <div className={styles.dot} style={{ left: `${row.v15.pct}%` }} /> : null}
              </div>
              {figure.mobile.ticks.map((tick) => (
                <span key={tick.label} className={styles.tick} style={{ left: `${tick.pct}%` }}>
                  {tick.label}
                </span>
              ))}
            </div>
            <p className={row.v14Past ? styles.readoutMiss : styles.readout}>
              {figure.mobile.v14Version} {row.v14Signed} · emp {row.v14Emp}
            </p>
            {row.v15 ? (
              <p className={styles.readout}>
                {figure.mobile.v15Version} {row.v15.signed} · emp {row.v15.emp}
                {row.v15.ci ? ` · CI ${row.v15.ci}` : ''}
                {row.v15.past ? <span className={styles.readoutNote}> · interval past the gate</span> : null}
              </p>
            ) : null}
          </article>
        ))}
      </div>
    </>
  );
}
