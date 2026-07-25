export interface TutorialScript {
  id: string;
  title: string;
  filename: string;
  description: string;
  source: string;
}

export const tutorials: TutorialScript[] = [
  {
    id: "01",
    title: "One agent, one scene",
    filename: "01-lamp.smith",
    description: "The simplest thing that runs. One agent, one scene, no choices.",
    source: `// Tutorial 01 — The simplest thing that runs.
// One agent, one scene, the entire budget goes to the one scene.

agent lamp {
  purpose minimise heat_residual
  scenes {
    scene glow serves heat_residual with radiate_hook
  }
  self {
    parts { filament, glass }
    separations { (filament, glass: 3) }
  }
  budget 1.0
  floor  2.0
}`,
  },
  {
    id: "02",
    title: "Two scenes: attention divides",
    filename: "02-clerk.smith",
    description: "Two scenes compete for attention. Water-filling is not equal splitting.",
    source: `// Tutorial 02 — Two scenes compete.
// The clerk divides attention between counter and filing.
// Water-filling gives more to the scene with steeper early returns.

agent clerk {
  purpose minimise backlog
  scenes {
    scene counter serves backlog with serve_hook
    scene filing  serves backlog with file_hook
  }
  self {
    parts { memory, manner, patience }
    separations {
      (memory, manner: 2), (manner, patience: 3), (patience, memory: 2)
    }
  }
  budget 1.0
  floor  2.0
}`,
  },
  {
    id: "03",
    title: "Five scenes: the threshold",
    filename: "03-operator.smith",
    description: "Five scenes compete. Some get dropped entirely when the budget is tight.",
    source: `// Tutorial 03 — Five scenes, one budget.
// Some scenes fall below the water level and get zero attention.

agent operator {
  purpose minimise queue_depth
  scenes {
    scene line_a      serves queue_depth with line_hook
    scene line_b      serves queue_depth with line_hook
    scene line_c      serves queue_depth with line_hook
    scene dispatch    serves queue_depth with dispatch_hook
    scene maintenance serves queue_depth with maint_hook
  }
  self {
    parts { focus, stamina, judgment, protocol }
    separations {
      (focus, stamina: 3), (stamina, judgment: 2),
      (judgment, protocol: 2), (protocol, focus: 2)
    }
  }
  budget 1.0
  floor  2.0
}`,
  },
  {
    id: "04",
    title: "Phase exclusion",
    filename: "04-phases.smith",
    description: "Construction and commitment alternate. Silence is productive.",
    source: `// Tutorial 04 — Phase exclusion.
// Watch the timeline: blue = construction (silent), orange = commitment.
// The agent goes quiet when it's forming new distinctions.

agent thinker {
  purpose minimise confusion
  scenes {
    scene read  serves confusion with read_hook
    scene write serves confusion with write_hook
  }
  self {
    parts { concept, expression, judgment }
    separations {
      (concept, expression: 3), (expression, judgment: 2),
      (judgment, concept: 2)
    }
  }
  budget 1.0
  floor  2.0
}`,
  },
  {
    id: "05",
    title: "History accumulates",
    filename: "05-archivist.smith",
    description: "The committed count never resets. Sessions accumulate.",
    source: `// Tutorial 05 — The monotone staircase.
// Run for 30 ticks: the count only goes up.
// A copy started at 0 is a different individual.

agent archivist {
  purpose minimise disorder
  scenes {
    scene catalog serves disorder with catalog_hook
    scene restore serves disorder with restore_hook
  }
  self {
    parts { memory, method, care }
    separations {
      (memory, method: 4), (method, care: 2), (care, memory: 3)
    }
  }
  budget 1.0
  floor  2.0
}`,
  },
  {
    id: "06",
    title: "Two agents coordinate",
    filename: "06-workshop.smith",
    description: "A smith and apprentice share a purpose. Disjoint internals, coordinated outcome.",
    source: `// Tutorial 06 — Coordination without shared internals.
// The smith and apprentice have nothing in common internally.
// But they share a purpose and their phases lock.

society workshop {
  agent smith {
    purpose minimise forge_residual
    scenes {
      scene hammer serves forge_residual with forge_hook
    }
    self {
      parts { skill, endurance }
      separations { (skill, endurance: 3) }
    }
    budget 1.0
    floor  2.0
  }
  agent apprentice {
    purpose minimise forge_residual
    scenes {
      scene bellows serves forge_residual with bellows_hook
    }
    self {
      parts { obedience, strength }
      separations { (obedience, strength: 2) }
    }
    budget 0.5
    floor  2.0
  }
  tie (smith, apprentice: 2)
  couple 3.0
}`,
  },
  {
    id: "07",
    title: "Crowd sharpening",
    filename: "07-crowd.smith",
    description: "More agents = lower collective failure. The crowd sharpens the purpose.",
    source: `// Tutorial 07 — Crowd sharpening.
// Five mediocre agents (q=0.6 each): collective failure = 0.6^5 ≈ 0.08.
// The crowd sharpens the purpose multiplicatively.

society guild {
  agent worker_1 {
    purpose minimise task_residual
    scenes { scene work serves task_residual with work_hook }
    self {
      parts { effort, skill }
      separations { (effort, skill: 2) }
    }
    budget 0.5
    floor  2.0
  }
  agent worker_2 {
    purpose minimise task_residual
    scenes { scene work serves task_residual with work_hook }
    self {
      parts { effort, skill }
      separations { (effort, skill: 2) }
    }
    budget 0.5
    floor  2.0
  }
  agent worker_3 {
    purpose minimise task_residual
    scenes { scene work serves task_residual with work_hook }
    self {
      parts { effort, skill }
      separations { (effort, skill: 2) }
    }
    budget 0.5
    floor  2.0
  }
  agent worker_4 {
    purpose minimise task_residual
    scenes { scene work serves task_residual with work_hook }
    self {
      parts { effort, skill }
      separations { (effort, skill: 2) }
    }
    budget 0.5
    floor  2.0
  }
  agent worker_5 {
    purpose minimise task_residual
    scenes { scene work serves task_residual with work_hook }
    self {
      parts { effort, skill }
      separations { (effort, skill: 2) }
    }
    budget 0.5
    floor  2.0
  }
  tie (worker_1, worker_2: 2)
  tie (worker_2, worker_3: 2)
  tie (worker_3, worker_4: 2)
  tie (worker_4, worker_5: 2)
  couple 4.0
}`,
  },
  {
    id: "08",
    title: "Society water-filling",
    filename: "08-society-attention.smith",
    description: "The society divides collective attention by the same law, one level up.",
    source: `// Tutorial 08 — Society-level water-filling.
// The workshop faces two shared purposes: forging and trading.
// The same water-filling law applies at both scales.

society market_workshop {
  agent smith {
    purpose minimise workshop_residual
    scenes {
      scene forge serves workshop_residual with forge_hook
      scene trade serves workshop_residual with trade_hook
    }
    self {
      parts { craft, commerce, reputation }
      separations {
        (craft, commerce: 3), (commerce, reputation: 2),
        (reputation, craft: 2)
      }
    }
    budget 1.0
    floor  2.0
  }
  agent merchant {
    purpose minimise workshop_residual
    scenes {
      scene trade serves workshop_residual with trade_hook
      scene source serves workshop_residual with source_hook
    }
    self {
      parts { negotiation, logistics, trust }
      separations {
        (negotiation, logistics: 2), (logistics, trust: 3),
        (trust, negotiation: 2)
      }
    }
    budget 0.8
    floor  2.0
  }
  tie (smith, merchant: 2)
  couple 3.0
}`,
  },
  {
    id: "09",
    title: "Natural language → DSL",
    filename: "09-prompt.smith",
    description: "Start from a prompt. The LLM writes the script; you shape the agent through charts.",
    source: `// Tutorial 09 — The prompt path.
// This script was generated from: "An agent that manages a restaurant,
// handling kitchen, front of house, and supply ordering, always short on time."
// Edit it, or reshape it through the charts.

agent restaurant_manager {
  purpose minimise operational_residual
  scenes {
    scene kitchen     serves operational_residual with kitchen_hook
    scene front_house serves operational_residual with service_hook
    scene ordering    serves operational_residual with supply_hook
  }
  self {
    parts { palate, presence, logistics, composure }
    separations {
      (palate, presence: 2), (presence, logistics: 3),
      (logistics, composure: 2), (composure, palate: 2)
    }
  }
  budget 0.7
  floor  2.0
}`,
  },
  {
    id: "10",
    title: "The iron smith",
    filename: "10-iron-smith.smith",
    description: "The full agent: purpose, four scenes, coherence constraint.",
    source: `// Tutorial 10 — The iron smith: a CHARACTER.
// Standing purpose, runs on. Four parts, three scenes, coherence keeps.

agent smith {
  purpose minimise forge_residual
  scenes {
    scene hammer   serves forge_residual with forge_hook
    scene contract serves forge_residual with contract_hook
    scene source   serves forge_residual with source_ore_hook
  }
  self {
    parts { skill, stock, orders, reputation }
    separations {
      (skill, stock: 3), (stock, orders: 2),
      (orders, reputation: 2), (reputation, skill: 2)
    }
  }
  budget 1.0
  floor  2.0
  coherence keeps { reputation, skill }
}`,
  },
];

export function getTutorialById(id: string): TutorialScript | undefined {
  return tutorials.find(t => t.id === id);
}

export function getTutorialByFilename(filename: string): TutorialScript | undefined {
  return tutorials.find(t => t.filename === filename);
}
