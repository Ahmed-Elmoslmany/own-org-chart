# Technologies
- React + Vite
# How to install
- Open terminal & hit `https://github.com/Ahmed-Elmoslmany/own-org-chart.git`
- Then `cd own-org-chart && npm install && npm run dev`
- Open server on http://localhost:5173/

# Features we are coverd
- Build Organization Chart
- Show the full tree view (zoom out for the whole tree)
- How to focus/zoom on specific part of the tree view
- How to handle Collapse/Expand tree nodes
- How to zoomIn/Out & pan (combination with another zooming & pan package)

# PRIMEREACT

## Pros
- Open-Source and Free: Available under the MIT license, no cost to use, accessible via npm install primereact.
- Wide Community: Over 10,000 GitHub stars, active forums, and a large user base as of April 2025.
- Always Supported: Maintained by PrimeTek with community and optional commercial support, ensuring reliability.
- Near Release: Regular updates (e.g., version 10.x in 2025), keeping it current and compatible with modern React.
- The OrganizationChart component natively supports hierarchical data visualization in vertical or horizontal layouts, making it straightforward to implement a tree view out of the box.
- Built-in expand/collapse functionality allows users to toggle sub-nodes with minimal effort, enhancing usability for large structures.
- Supports dynamic node addition by updating the data structure (e.g., adding children, parents, or siblings), which can partially meet directional requirements based on layout (vertical: up/down; horizontal: left/right).
- Can be customized with React code (e.g., CSS transform: scale() or libraries like react-zoom-pan-pinch), offering flexibility for developers willing to extend functionality.

## Cons
- No native zoom support in OrganizationChart, necessitating custom implementation with CSS transforms or external libraries, increasing development time and complexity.
- Layouts are fixed (vertical or horizontal), limiting flexibility compared to libraries with dynamic positioning, potentially misaligning with custom designs.
- Visual positioning depends on the layout algorithm, not manual placement, making precise directional additions (e.g., left vs. right) challenging without deep data manipulation.
