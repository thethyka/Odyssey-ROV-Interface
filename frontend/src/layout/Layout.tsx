import Header from "./Header.tsx";
import LeftSidebar from "./LeftSidebar.tsx";
import MainContent from "./MainContent.tsx";
import RightSidebar from "./RightSidebar.tsx";

export default function Layout() {
  return (
    <div className="box flex flex-col border-green-500 border-2 min-h-svh">
      <Header />

      <main className="main grow border-blue-500 border-2 flex flex-row">
        <LeftSidebar />
        <MainContent />
        <RightSidebar />
      </main>
    </div>
  );
}
