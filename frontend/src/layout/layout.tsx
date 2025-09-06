import Header from "./Header.tsx"


export default function Layout() {
  return (
    <div className="box flex flex-col border-green-500 border-2 min-h-svh">
      <header className="header h-30 border-red-500 border-2"></header>

      <main className="main grow border-blue-500 border-2 flex flex-row justify-between">
        <section className="sidebar w-80 border-red-500 border-2"></section>

        <section className="main-content grow border-red-500 border-2"></section>

        <section className="history w-60 border-red-500 border-2"></section>
      </main>
    </div>
  );
}
