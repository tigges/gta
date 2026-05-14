export interface Game {
  id: string;
  title: string;
  short: string;
  year: number | null;
  published: boolean;
  dataDir: string;
}

export const GAMES: Game[] = [
  { id: 'gta-1',  title: 'Grand Theft Auto',             short: 'GTA 1',  year: 1997, published: false, dataDir: 'gta-1'  },
  { id: 'gta-2',  title: 'Grand Theft Auto 2',            short: 'GTA 2',  year: 1999, published: false, dataDir: 'gta-2'  },
  { id: 'gta-3',  title: 'Grand Theft Auto III',          short: 'GTA III',year: 2001, published: false, dataDir: 'gta-3'  },
  { id: 'gta-vc', title: 'Grand Theft Auto: Vice City',   short: 'GTA VC', year: 2002, published: false, dataDir: 'gta-vc' },
  { id: 'gta-sa', title: 'Grand Theft Auto: San Andreas', short: 'GTA SA', year: 2004, published: false, dataDir: 'gta-sa' },
  { id: 'gta-4',  title: 'Grand Theft Auto IV',           short: 'GTA IV', year: 2008, published: false, dataDir: 'gta-4'  },
  { id: 'gta-5',  title: 'Grand Theft Auto V',            short: 'GTA V',  year: 2013, published: true,  dataDir: 'gta-5'  },
  { id: 'gta-6',  title: 'Grand Theft Auto VI',           short: 'GTA VI', year: null, published: true,  dataDir: 'gta-6'  },
];

export const PUBLISHED_GAMES = GAMES.filter((g) => g.published);
export const ALL_GAMES = GAMES;
