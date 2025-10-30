import React from 'react'
import './App.css'
import InsuranceAgentFrontend from './components/InsuranceAgentFrontend.jsx'

function App() {
  const [count, setCount] = React.useState(0)

  return (
    <div>
      <InsuranceAgentFrontend />
    </div>
  )
}

export default App