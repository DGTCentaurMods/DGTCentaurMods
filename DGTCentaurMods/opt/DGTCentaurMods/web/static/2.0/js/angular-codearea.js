/*
 * Lightweight textarea syntax highlighter for AngularJS
 * (C) 2016 Ingo van Lil <inguin@gmx.de>
 *
 * Based upon LDT (http://kueblc.github.io/LDT/)
 * (C) 2012 Colin Kuebler <kueblc@rpi.edu>
 */

angular
    .module('ivl.angular-codearea', ['ng'])
    .directive('ivlCodearea', function() {
	// directive template: transparent textarea in front of a <pre> layer with highlighted text
        var template =
            '<div class="codearea">' +
            '  <pre><span ng-repeat="token in tokens" ng-class="token.class" ng-bind="token.text"></span>' +
            '  </pre>' +
            '  <textarea ng-model="ngModel" ng-trim="false" spellcheck="false"></textarea>' +
            '</div>';

	// default rules: no highlighting
        var DEFAULT_RULES = {
            whitespace: /\s+/,
            other: /\S+/
        };

	// example highlighting rules for Lua code
        var UCI_RULES = {
            whitespace: /\s+/,
            comment: /--.*/,
            op: /[#%\(\)\*\+,-\./:;<=>\[\]\{\}]/,
            keyword: /(and|break|do|else|elseif|end|false|for|function|if|in|local|nil|not|or|repeat|require|return|then|true|until|while)(?![a-zA-Z0-9_])/,
            function: /(assert|collectgarbage|error|ipairs|pcall|print|printTable|string\.find|string\.format|string\.len|string\.lower|string\.match|string\.reverse|string\.sub|string\.upper|table\.concat|table\.insert|table\.remove|table\.sort|tonumber|tostring|type|unpack)(?![a-zA-Z0-9_])/,
            id: /[a-zA-Z_][a-zA-Z0-9_]*/,
            number: /[0-9]+(\.[0-9]+)?|\.[0-9]+/,
            string: /"[^"]*"?/,
            other: /\S+/
        };

	// maps value of the "syntax" attribute to a set of rules
        var RULES = {
            uci: UCI_RULES
        };

        return {
            restrict: 'E',
            template: template,
            scope: { ngModel: '=', syntax: '@' },
            link: function(scope) {
                scope.tokens = [];

                var rules = RULES[scope.syntax] || DEFAULT_RULES;
                var ruleSrcs = [];
                var ruleMap = {};

                for (var rule in rules) {
                    var src = rules[rule].source;
                    ruleSrcs.push(src);
                    ruleMap[rule] = new RegExp('^(' + src + ')$');
                }
                var parseRe = new RegExp(ruleSrcs.join('|'), 'g');

                function identify(token) {
                    for (var rule in ruleMap) {
                        if (ruleMap[rule].test(token)) return rule;
                    }
                    return "other";
                }

                function update(text) {
                    text = text || "";
                    var results = text.match(parseRe) || [];

                    // count unchanged tokens from the front, remove from results
                    var firstDiff = 0;
                    while (firstDiff < scope.tokens.length &&
                           firstDiff < results.length &&
                           scope.tokens[firstDiff].text === results[firstDiff])
                    {
                        ++firstDiff;
                    }
                    results.splice(0, firstDiff);

                    // count unchanged tokens from the rear, pop from results
                    var lastDiff = scope.tokens.length - 1;
                    while (lastDiff > firstDiff &&
                           results.length > 0 &&
                           scope.tokens[lastDiff].text == results[results.length - 1])
                    {
                        --lastDiff;
                        results.pop();
                    }

                    // replace changed tokens with new ones
                    var newTokens = results.map(function(token) {
                        return { text: token, class: identify(token) };
                    });

                    // limit number of DOM elements to be generated per digest cycle to
                    // avoid stalling slower browsers
                    var MAX_NEW_TOKENS = 50;
                    if (newTokens.length > MAX_NEW_TOKENS) {
                        newTokens.splice(MAX_NEW_TOKENS);
                        setTimeout(() => update(text));
                    }

                    // ES6: scope.tokens.splice(firstDiff, lastDiff - firstDiff + 1, ...newTokens);
		    scope.tokens.splice.apply(scope.tokens, [firstDiff, lastDiff - firstDiff + 1].concat(newTokens));

                    scope.$applyAsync();
                }

                scope.$watch('ngModel', update);
            }
        }
    });
