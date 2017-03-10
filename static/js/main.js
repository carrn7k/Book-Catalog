// sticky search bar
$(document).ready(function() {

	$(document).on("scroll", function() {

		var searchWrap = $(".srchWrap");
		var loginLogout = $("#login-logout");

		if ($(document).scrollTop() > 200 && 
			$(document).width() < 600 ) {
				searchWrap.addClass("srchWrapFixed");
				console.log($(document).width());
				loginLogout.hide()
		} else {
			searchWrap.removeClass("srchWrapFixed");
			loginLogout.show();
		}
	});
})

// jQuery autocomplete search bar
$(document).ready(function() {
	var bookList = $("#search-list").data("books");
	var searchBar = $("#autocomplete");

	searchBar.autocomplete({
  		source: bookList,
  		select: function(event, ui) {
  			console.log(ui.item.value);
  			event.preventDefault();
  			window.location.href = "/catalog/" + ui.item.value + "/book/"
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
		if (model.bookData) {
			model.currentBook = model.bookData[0];
			bookView.init();
		}
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

		// current book view (large screen)
		this.cTitle = $("#current-title");
		this.cAuthor = $("#current-author");
		this.cSummary = $("#current-summary");
		this.cPhoto = $("#current-photo");
		this.editDeleteWrap = $("#edit-delete");
		this.cEdit = $("#edit-book");
		this.cDelete = $("#delete-book");


		// current book view (modal)
		this.modal = $("#modal");
		this.modalClose = $("#modal-close");
		this.modPhoto = $("#modal-img");
		this.modTitle = $("#modal-title");
		this.modAuthor = $("#modal-author");
		this.modSummary = $("#modal-summary");
		this.editDeleteModal = $("#edit-dlt-mdl");
		this.modEdit = $("#edit-mdl");
		this.modDelete = $("#delete-mdl");

		this.render(false);
	},
	render: function(modalStatus) {

		var currentBook = controller.getCurrentBook();
		var width = $(document).width();


		// Current Genre (Large Screens)
		this.cTitle.text(currentBook.title);
		this.cAuthor.text("Written by -- " + currentBook.author);
		this.cSummary.text(currentBook.summary);
		this.cPhoto.attr("src", currentBook.book_photo);

		// Current Genre (Small Screens)
		this.modPhoto.attr("src", currentBook.book_photo);
		this.modTitle.text(currentBook.title);
		this.modAuthor.text("Written by -- " + currentBook.author);
		this.modSummary.text(currentBook.summary);

		// Don't render the modal on page load
		if (modalStatus == true)
			this.modal.show();



		// If user is logged in and the creator of the current book
		// display edit and delete options

		if (currentBook.user_id == currentBook.c_user_id) {

			var editUrl = '/catalog/' + currentBook.book_id + '/book/edit/';
			var deleteUrl = '/catalog/' + currentBook.book_id + '/book/delete/';

			this.cEdit.attr('href', editUrl);
			this.cDelete.attr('href', deleteUrl);

			this.modEdit.attr('href', editUrl);
			this.modDelete.attr('href', deleteUrl);

			this.editDeleteModal.show();
			this.editDeleteWrap.show();
		}
		else {
			this.editDeleteModal.hide();
			this.editDeleteWrap.hide();
		}

		// set click events for the booklist
		self = this;

		this.bookList.each(function(i, book) {

			var books = controller.getBooks();
			var bookID = $( this ).data("id");

			$( this ).on("click", function() {

				self.modal.hide();

				if (bookID) {
					currentBook = books.filter(function(book) {
						return book.book_id == bookID
					});
					if (currentBook) {
						controller.setCurrentBook(currentBook[0]);
						self.render(true);	
					}
				}
			})
		})

		// Close Modal Event
		this.modalClose.on("click", function() {
			self.modal.hide();
		})
	}
}

controller.init();
})

