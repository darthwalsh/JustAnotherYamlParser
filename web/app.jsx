"use strict";

class App extends React.Component {
  constructor(props) {
    super(props);
    this.state = {rule: "nb-double-one-line", text: "", success: true, result: ""};
  }

  clickRun = async () => {
    var request = await fetch("values", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(this.state),
    });
    // Don't use HTTP error code because you can't catch that using babel compiled code...?
    const {success, result} = await request.json();
    this.setState({success, result: success ? JSON.stringify(result, null, 2) : result});
  };

  onChange = e => this.setState({[e.target.name]: e.target.value});

  render() {
    return (
      <div>
        JustAnotherYamlParser
        <button id="run" onClick={this.clickRun}>
          Run
        </button>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gridGap: "10px",
            height: "100%",
          }}
        >
          <div>
            Rule: <input name="rule" value={this.state.rule} onChange={this.onChange} />
            <br />
            Input: <br />
            <textarea name="text" onChange={this.onChange} />
          </div>
          <div id="output">
            <pre style={{color: this.state.success ? "black" : "red"}}>{this.state.result}</pre>
          </div>
        </div>
      </div>
    );
  }
}

ReactDOM.render(<App />, document.querySelector("#container"));
