import "./App.css";
import { useState } from "react";
import { OrganizationChart } from "primereact/organizationchart";
import { TransformWrapper, TransformComponent } from "react-zoom-pan-pinch";

function App() {
  const [data, setData] = useState([
    {
      label: "Argentina",
      expanded: true,
      children: [
        {
          label: "Argentina",
          expanded: true,
          children: [
            {
              label: "Argentina",
              expanded: true,
              children: [
                {
                  label: "France",
                  expanded: true,

                  children: [
                    {
                      label: "France",
                      expanded: true,
                    },
                    {
                      label: "Morocco",
                      expanded: true,
                    },
                  ],
                },
                {
                  label: "Morocco",
                  expanded: true,
                },
              ],
            },
            {
              label: "Croatia",
              expanded: true,
              children: [
                {
                  label: "France",
                  expanded: true,

                  children: [
                    {
                      label: "France",
                      expanded: true,
                    },
                    {
                      label: "Morocco",
                      expanded: true,
                    },
                  ],
                },
                {
                  label: "Morocco",
                  expanded: true,
                },
              ],
            },
          ],
        },
        {
          label: "France",
          expanded: true,
          children: [
            {
              label: "France",
              expanded: true,

              children: [
                {
                  label: "France",
                  expanded: true,
                },
                {
                  label: "Morocco",
                  expanded: true,
                },
              ],
            },
            {
              label: "Morocco",
              expanded: true,
            },
          ],
        },
      ],
    },
  ]);

  const addNode = (e) => {
    console.log(e.node);
    e.node.expanded = true;
    const newNode = {
      label: "New Node",
      expanded: true,
      children: [],
    };

    if (e.node.children) {
      e.node.children.push(newNode); // Add node on right side
      e.node.expanded = true;
      //   e.node.children.unshift(newNode); // Add node on left side
    } else {
      e.node.children = [newNode];
    }

    setData([...data]);
  };

  return (
    <div className="w-full h-screen">
      <TransformWrapper
        initialScale={1}
        minScale={0.5}
        maxScale={3}
        wheel={{ step: 0.1 }}
        doubleClick={{ disabled: true }}
        className="w-full h-screen"
      >
        {({ zoomIn, zoomOut, resetTransform }) => (
          <>
            <div className="zoom-controls">
              <button onClick={() => zoomIn()}>ZoomIn | </button>
              <button onClick={() => zoomOut()}> ZoomOut |</button>
              <button onClick={() => resetTransform()}> Reset</button>
            </div>
            <TransformComponent
              wrapperClass="w-full h-full"
              contentClass="flex items-center justify-center"
            >
              <div className="p-8">
                <OrganizationChart
                  value={data}
                  className="w-full h-full"
                  selectionMode="single"
                  onNodeSelect={addNode}
                  //   onNodeUnselect={} // TODO: Toggle node selection
                />
              </div>
            </TransformComponent>
          </>
        )}
      </TransformWrapper>
    </div>
  );
}

export default App;
