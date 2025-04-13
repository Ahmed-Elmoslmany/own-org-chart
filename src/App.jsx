import "./App.css";
import { useState } from "react";
import { OrganizationChart } from "primereact/organizationchart";
import { TransformWrapper, TransformComponent } from "react-zoom-pan-pinch";


function App() {
  const [data, setData] = useState(
    [
      {
        "id": "23c15371-fd9b-44b8-9281-097cdc61da7f",
        "label": "ceo",
        "parent_id": null,
        "children": [
          {
            "id": "5058da83-4d3a-44a2-8b96-5f4220e0e147",
            "label": "node_1",
            "parent_id": "23c15371-fd9b-44b8-9281-097cdc61da7f",
            "children": [
              {
                "id": "60c1b1ae-5a5f-46bf-869b-7b12d820259c",
                "label": "node_4",
                "parent_id": "5058da83-4d3a-44a2-8b96-5f4220e0e147",
                "children": []
              },
              {
                "id": "3f6e7fb5-e888-4200-8d40-5713c3507023",
                "label": "node_9",
                "parent_id": "5058da83-4d3a-44a2-8b96-5f4220e0e147",
                "children": []
              }
            ]
          },
          {
            "id": "bf90f75a-f83e-48e8-9342-1617aa478e4e",
            "label": "node_2",
            "parent_id": "23c15371-fd9b-44b8-9281-097cdc61da7f",
            "children": [
              {
                "id": "a2d5f3e4-c9c4-41b9-a1b4-6f800c4d57a2",
                "label": "node_5",
                "parent_id": "bf90f75a-f83e-48e8-9342-1617aa478e4e",
                "children": []
              }
            ]
          },
          {
            "id": "7ec52a6c-35c5-4bb8-b40b-8f6c5b960103",
            "label": "node_3",
            "parent_id": "23c15371-fd9b-44b8-9281-097cdc61da7f",
            "children": []
          },
          {
            "id": "1283db05-bb30-41e7-a4cb-d180982e8f2e",
            "label": "node_6",
            "parent_id": "23c15371-fd9b-44b8-9281-097cdc61da7f",
            "children": []
          },
          {
            "id": "107ee96d-d87b-455b-9956-6e79e1d7f1ab",
            "label": "node_7",
            "parent_id": "23c15371-fd9b-44b8-9281-097cdc61da7f",
            "children": [
              {
                "id": "6992b7b9-78a6-450b-b44f-e8248dfb4e8b",
                "label": "node_8",
                "parent_id": "107ee96d-d87b-455b-9956-6e79e1d7f1ab",
                "children": []
              }
            ]
          }
        ]
      }
    ]
    
  );

  const addNode = (e) => {
    const newNode = {
      label: "New Node",
      expanded: true,
      children: [],
    };

    if (e.node.children) {
      e.node.children.push(newNode); // Add node on right side
      //   e.node.children.unshift(newNode); // Add node on left side
    } else {
      e.node.children = [newNode];
    }

    setData([...data]);
  };

  return (
    <div
      style={{
        width: "100vw",
        height: "100vh",
      }}
    >
      <TransformWrapper
        initialScale={1}
        minScale={0.1}
        maxScale={3}
        wheel={{ step: 0.1 }}
        doubleClick={{ disabled: true }}
        limitToBounds={false}
        centerOnInit={true}
      >
        {({ zoomIn, zoomOut, resetTransform }) => (
          <>
            <div
              style={{
                background: "white",
                padding: "8px",
                borderRadius: "4px",
              }}
            >
              <button onClick={() => zoomIn()}>Zoom In</button>
              <button onClick={() => zoomOut()}>Zoom Out</button>
              <button onClick={() => resetTransform()}>Reset</button>
            </div>

            <TransformComponent
              wrapperStyle={{
                width: "100%",
                height: "100vh",
              }}
              contentStyle={{
                width: "fit-content",
                height: "fit-content",
              }}
            >
              <div
               
              >
                <OrganizationChart
                  value={data}
                  collapsible={true}
                  selectionMode="single"
                  onNodeSelect={addNode}
                />
              </div>
            </TransformComponent>
          </>
        )}
      </TransformWrapper>
    </div>
  );
}

export default App