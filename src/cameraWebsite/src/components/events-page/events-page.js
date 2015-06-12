define(['knockout', 'text!./events-page.html', 'client', 'router', 'jquery'], function (ko, templateMarkup, client, router, jquery) {

    function EventsPage(params) {
        var self = this;

        self.search = {
            after: ko.observable(),
            before: ko.observable(),
            after_offset: ko.observable(),
            before_offset: ko.observable(),
            event_type: ko.observable(),
            limit: ko.observable(20),
            skip: ko.observable()
        };

        self.meta = ko.observableArray();

        /**
         * Computed value, maps between the numeric value actually held in the search observable
         * and the date model required by the various UI components.
         */
        self.afterOffsetDate = client.wrapTimeOffsetObservable(self.search.after_offset);
        self.beforeOffsetDate = client.wrapTimeOffsetObservable(self.search.before_offset);

        /**
         * Used to set up the range shown by the time picker
         */
        self.minTime = new Date(2000, 0, 1, 15, 0, 0);
        self.maxTime = new Date(2000, 0, 1, 10, 0, 0);

        self.results = ko.observableArray();
        self.resultCount = ko.observable(0);
        self.firstResultIndex = ko.observable(0);
        self.pages = ko.observableArray();
        self.hasQuery = ko.observable();

        self.urlForFile = client.urlForFile;
        self.filenameForFile = client.filenameForFile;

        /**
         * Function called from the UI to remove the given meta constraint from the list
         * @param meta
         */
        self.removeMeta = function (meta) {
            self.meta.remove(meta);
        };

        if (params.search) {
            // Configure the observable from the search
            client.populateObservables(self.search, params.search, {
                "before": "date",
                "after": "date"
            });
            // Configure the observable array of file meta
            var sourceMeta = client.decodeString(params.search)['meta_constraints'];
            if (sourceMeta) {
                ko.utils.arrayForEach(sourceMeta, function (meta) {
                    var type = meta['type'];
                    var isNumber = (type == "less" || type == "greater" || type == "number_equals");
                    var isDate = (type == "after" || type == "before");
                    var isString = (type == "string_equals");
                    d = {
                        type: ko.observable(type),
                        key: ko.observable(meta['key']),
                        string_value: ko.observable(isString ? meta['value'] : ''),
                        date_value: ko.observable(isDate ? new Date(meta['value'] * 1000) : new Date(Date.now())),
                        number_value: ko.observable(isNumber ? meta['value'] : 0)
                    };
                    self.meta.push(d);
                });
            }

            // Get the search object and use it to retrieve results
            var search = client.toJSRemovingDefaults(self.getSearchObject());
            var skip = search.hasOwnProperty("skip") ? search.skip : 0;
            // Reset the skip parameter, if any
            self.search.skip(0);
            client.searchEvents(search, function (error, results) {
                self.results(results.events);
                self.resultCount(results.count);
                self.firstResultIndex(skip);
                var pages = [];
                // Only do pagination if we have a search limit
                if (search.limit > 0 && (skip > 0 || results.events.length < results.count)) {
                    var i = 0;
                    while (i < results.count) {
                        var newSearch = jquery.extend(true, {}, search);
                        newSearch.skip = i;
                        var page = {
                            from: i + 1,
                            to: Math.min(i + search.limit, results.count) + 1,
                            search: newSearch,
                            current: (skip == newSearch.skip)
                        };
                        pages.push(page);
                        i += search.limit;
                    }
                }
                self.pages(pages);
                self.hasQuery(true);
            });

        } else {
            self.hasQuery(false);
        }

    }

    EventsPage.prototype.addMeta = function () {
        var self = this;
        self.meta.push({
            type: ko.observable('string_equals'),
            key: ko.observable('meteorpi:meta_key_1'),
            string_value: ko.observable('meta_value_1'),
            date_value: ko.observable(new Date(Date.now())),
            number_value: ko.observable(0)
        });
    };

    EventsPage.prototype.getSearchObject = function () {
        var self = this;
        // Build the appropriate file meta query to send to the server
        var meta = self.meta.map(function (m) {
            var func = {};
            var type = ko.unwrap(m.type);
            if (type == "string_equals") {
                func.value = ko.unwrap(m.string_value);
                if (func.value.length == 0) {
                    func.value = null;
                }
            } else if (type == "after" || type == "before") {
                if (ko.unwrap(m.date_value) != null) {
                    func.value = ko.unwrap(m.date_value).getTime() / 1000.0;
                } else {
                    func.value = null;
                }
            } else if (type == "less" || type == "greater" || type == "number_equals") {
                func.value = ko.unwrap(m.number_value);
            }
            if (func.value == null) {
                return null;
            }
            return {
                key: ko.unwrap(m.key),
                type: type,
                value: func.value
            }
        }).filter(function (m) {
            return m != null;
        });
        var search = jquery.extend({}, self.search, {meta_constraints: meta});
        return search;
    };

    EventsPage.prototype.changePage = function () {
        router.goTo("events", {"search": client.stringFromObservables(this.search)});
    };

    EventsPage.prototype.searchEvents = function () {
        var self = this;
        router.goTo("events", {"search": client.stringFromObservables(self.getSearchObject())})
    };

    // This runs when the component is torn down. Put here any logic necessary to clean up,
    // for example cancelling setTimeouts or disposing Knockout subscriptions/computeds.
    EventsPage.prototype.dispose = function () {
        jquery("body > div").slice(1).remove();
    };

    return {viewModel: EventsPage, template: templateMarkup};

});
