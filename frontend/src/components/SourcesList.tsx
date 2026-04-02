import type { Source } from '../services/agentApi'
interface SourcesListProps {
  sources: Source[];
}

export const SourcesList = ({ sources }: SourcesListProps) => {
  if (!sources.length) return null;

  return (
    <div style={{ marginTop: '12px', padding: '12px', backgroundColor: '#F8F8F8', borderRadius: '8px', borderLeft: '3px solid #FDDA24' }}>
      <p style={{ fontSize: '11px', fontWeight: 600, color: '#666', margin: '0 0 8px 0', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
        Fuentes consultadas
      </p>
      {sources.map((source, index) => (
        <div key={index} style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', marginBottom: '6px' }}>
          <span style={{ backgroundColor: '#FDDA24', color: '#000', fontSize: '10px', fontWeight: 700, padding: '2px 6px', borderRadius: '4px', minWidth: '20px', textAlign: 'center' }}>
            {index + 1}
          </span>
          <div>
            <a href={source.url} target="_blank" rel="noopener noreferrer" style={{ fontSize: '12px', color: '#0066CC', textDecoration: 'none', fontWeight: 500 }}>
              {source.title || source.url}
            </a>
            <span style={{ fontSize: '11px', color: '#999', marginLeft: '8px', backgroundColor: '#EFEFEF', padding: '1px 6px', borderRadius: '10px' }}>
              {source.category}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
};