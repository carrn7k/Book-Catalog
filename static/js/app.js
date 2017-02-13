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

		$(document).ready(function() {
			var navContainer = $(".navWrap");
			$("#genre-button").on("click", function() {
				navContainer.toggleClass("navDisplay");
			});
		})

		// GoogleAuth script
		function start() {
			gapi.load('auth2', function() {
			auth2 = gapi.auth2.init({
			client_id: '348313489050-u609qlb0cb5pjo1kib9eilsreh5i0fed.apps.googleusercontent.com',
          // Scopes to request in addition to 'profile' and 'email'
          //scope: 'additional_scope'
        });
      });
		$(document).ready(start());
    }