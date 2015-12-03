define(['knockout', 'text!./search-editor.html', 'utils', 'jquery', 'client'], function (ko, templateMarkup, utils, jquery, client) {

    function SearchEditor(params, componentInfo) {
        var self = this;

        // Set up tooltips
        self.showHelp = false;

        $('[data-toggle="tooltip"]', $(componentInfo.element)).tooltip({'placement':'right'});

        $('#searchtype').click(function() {
            $('[data-toggle="tooltip"]', $(componentInfo.element)).tooltip({'placement':'right'});
        });

        $('.help-toggle', $(componentInfo.element)).click(function() {
            self.showHelp = !self.showHelp;
            $('[data-toggle="tooltip"]', $(componentInfo.element)).tooltip({'placement':'right'});
            $('[data-toggle="tooltip"]', $(componentInfo.element)).tooltip( self.showHelp ? "show" : "hide");
        });

        // Available cameras
        self.cameras = params.cameras;
        self.searchTypes = params.searchTypes;

        self.search = params.search;
        if (params.hasOwnProperty('onSearch')) {
            self.performSearch = params.onSearch;
        } else {
            self.performSearch = false;
        }

        /**
         * Used to set up the range shown by the time picker
         */
        self.minTime = new Date(2000, 0, 1, 15, 0, 0);
        self.maxTime = new Date(2000, 0, 1, 10, 0, 0);

        /**
        self.removeMeta = function (meta) {
            console.log(self);
            self.search.meta.remove(meta);
        };

        self.addMeta = function () {
            self.search.meta.push({
                type: ko.observable('string_equals'),
                key: ko.observable('meteorpi:meta_key_1'),
                string_value: ko.observable('meta_value_1'),
                date_value: ko.observable(new Date(Date.now())),
                number_value: ko.observable(0)
            });
        };
         */
    }

    // This runs when the component is torn down. Put here any logic necessary to clean up,
    // for example cancelling setTimeouts or disposing Knockout subscriptions/computeds.
    SearchEditor.prototype.dispose = function () {
        jquery("body > div").slice(1).remove();
    };

    return {viewModel: {createViewModel: function (params, componentInfo) {
                return new SearchEditor(params, componentInfo);
            }
        }, template: templateMarkup, synchronous: true};

});
