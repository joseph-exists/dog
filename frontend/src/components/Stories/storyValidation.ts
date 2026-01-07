// import type { StoryNode } from '../client/types';

// // I DON'T THINK THIS IS NECESSARY.  THIS IS SOLVABLE SIMPLY BY HAVING FORM FIELDS REQUIRED

// export interface ValidationResult {
//   isValid: boolean;
//   errors: string[];
//   warnings: string[];
// }

// export function validateStoryForPublish(nodes: StoryNode[]): ValidationResult {
//   const errors: string[] = [];
//   const warnings: string[] = [];

//   // Check for start node
//   const startNodes = nodes.filter(n => n.is_start_node);
//   if (startNodes.length === 0) {
//     errors.push('Story must have exactly one start node');
//   } else if (startNodes.length > 1) {
//     errors.push(`Story has ${startNodes.length} start nodes, must have exactly one`);
//   }

//   // Check for end nodes
//   const endNodes = nodes.filter(n => n.is_end_node);
//   if (endNodes.length === 0) {
//     warnings.push('Story has no end nodes - players cannot complete it');
//   }

//   // Check for orphan nodes (nodes with no incoming edges, except start)
//   // TODO: Review against existing node-choice implementation

//   return {
//     isValid: errors.length === 0,
//     errors,
//     warnings
//   };
// }