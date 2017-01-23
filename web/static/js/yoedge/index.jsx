class ComicItemView extends React.Component {
	constructor(props) {
		super(props); 
	}
	
	go2DetailPage() {
		window.location.href = "/comic/" + this.props.id
	}
	
	render() {
		return (
			<div className="index-comic" onClick={this.go2DetailPage.bind(this)}>
				<img src={YoedgeUtils.toCoverUrl(this.props.id)}></img>
				<div>
					<span className="name">{this.props.name}</span>
					<span className="author">作者：{this.props.author}</span>
					<span className="description">{this.props.description}</span>
				</div>
			</div>
		);
	}
}

class ComicsView extends React.Component {
	constructor(props) {
		super(props);
	}
	
	toChapter() {
		console.log('toChpater clicked')
		window.location.href = "/chapter/123"
	}
	
	render() {
		return (
			<div>
				<ComicItemView id="1000536" name="三只小魔怪" author="丁小咪粑粑" description="咪仔、小肥肥、细细粒"/>
			</div>
		);
	}
}


console.log('asdfasdfasdf')
let testView = ReactDOM.render(<ComicsView />, document.getElementById('test-react'));
window.TestView = testView;
