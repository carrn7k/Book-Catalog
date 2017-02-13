// sticky search bar
$(document).ready(function() {

	$(document).on("scroll", function() {

		var searchWrap = $(".srchWrap");

		if ($(document).scrollTop() > 200) {
			searchWrap.addClass("srchWrapFixed");
		} else {
			searchWrap.removeClass("srchWrapFixed");
		}
	});
})

// nav functions
$(document).ready(function() {

	var navContainer = $(".navWrap");
		subContainer = $(".nav-bar ul li").first();
		subMenu = $(".nav-bar ul li").first().find("ul");

	// Display the Nav Menu
	$("#genre-button").on("click", function() {
		navContainer.toggleClass("navDisplay");
	});

	// Display and hide submenus 
	subContainer.on("click", function() {
		if (subMenu.is(":visible") == false)
			subMenu.show();
		else
			subMenu.hide();
	})
})



// Highlighted Book Controller
$(function() {
var model = { 
	currentBook: null,
	bookData: $("#genre-container").data("books")
}

var controller = {
	init: function() {
		model.currentBook = model.bookData[0];
		bookView.init();
	},
	getBooks: function() {
		return model.bookData
	},
	getCurrentBook: function() {
		return model.currentBook
	},
	setCurrentBook: function(book) {
		model.currentBook = book;
	}
}

var bookView = {
	init: function() {

		// book list
		this.bookList = $(".genre-item");

		// current book view
		this.cTitle = $("#current-title");
		this.cAuthor = $("#current-author");
		this.cSummary = $("#current-summary");

		this.render();
	},
	render: function() {
		var currentBook = controller.getCurrentBook();
		
		this.cTitle.text(currentBook.title);
		this.cAuthor.text(currentBook.author);
		this.cSummary.text(currentBook.summary);

		// set click events for the booklist
		self = this;

		this.bookList.each(function(i, book) {

			var books = controller.getBooks();
			var bookID = $( this ).data("id");

			$( this ).on("click", function() {
				if (bookID) {
					currentBook = books.filter(function(book) {
						return book.book_id == bookID
					});
					if (currentBook) {
						controller.setCurrentBook(currentBook[0]);
						self.render();	
					}
				}
			})
		})
	}
}

controller.init();
})
