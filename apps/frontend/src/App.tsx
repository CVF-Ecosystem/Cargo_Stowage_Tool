import { useEffect, useState } from "react";
import Workspace from "./features/Workspace";
import ReportPage from "./features/ReportPage";

const REPORT_ROUTE = /^#\/report\/([0-9a-f-]{36})$/;

export default function App() {
  const [hash, setHash] = useState(() => window.location.hash);
  useEffect(() => {
    const onHash = () => setHash(window.location.hash);
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);
  const match = REPORT_ROUTE.exec(hash);
  if (match) return <ReportPage key={match[1]} id={match[1]} />;
  return <Workspace />;
}
