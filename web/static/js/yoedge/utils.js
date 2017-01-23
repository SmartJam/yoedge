
var module = (function() {
	var IMG_HOST = "http://oji3qlphh.bkt.clouddn.com/";
	
	return {
		toCoverUrl: function(comicId) {
			return IMG_HOST + "/covers/" + comicId + ".jpg"
		},

		toImgUrl: function(chapterId, imgCount) {
			imgIdx = ("000" + imgCount).slice(-3)
			return IMG_HOST + "/chapters/" + chapterId + "/" + imgIdx + ".jpg" 
		}
	}
}());

window.YoedgeUtils = module