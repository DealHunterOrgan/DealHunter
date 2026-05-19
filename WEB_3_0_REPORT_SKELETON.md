# DealHunter Web 3.0 Delivery Report Skeleton

## 1. Objective

The objective of this delivery is to add semantic markup to DealHunter using RDFa and schema.org vocabularies, following the official Django Web 3.0 RDFa tutorial provided by the teacher.

The required feature is semantic markup in one detail page for a domain entity. In DealHunter, the selected domain entity is the `Game`, represented in the application by the game detail page.

Main validated example:

- Page: `/game/2/`
- Entity: `ALL WILL FALL`
- Main template: `games/templates/games/detail.html`

## 2. Relation With The Official Tutorial

The official tutorial explains how to add RDFa markup to a Django detail template using schema.org vocabulary. The tutorial example uses a restaurant detail page with reviews and aggregate ratings.

DealHunter follows the same structure, adapted to the videogame/deals domain:

| Tutorial example | DealHunter equivalent |
| --- | --- |
| `Restaurant` | `VideoGame` / `Product` |
| Restaurant detail page | Game detail page |
| Restaurant name | Game title |
| Reviews | Game comments/reviews |
| Review rating | Game review rating |
| Aggregate rating | Average game review rating |
| Author | Review author |
| Date published | Review creation date |

## 3. Implemented Files

The main changes were implemented in:

- `games/templates/games/detail.html`
- `games/templates/games/home.html`
- `games/views.py`

## 4. Detail Page RDFa Implementation

The game detail page was marked as a semantic schema.org entity using RDFa:

```html
vocab="https://schema.org/"
typeof="VideoGame Product"
```

The following fields were marked semantically:

| DealHunter data | RDFa/schema.org markup |
| --- | --- |
| Game title | `property="name"` |
| Game page URL | `property="url"` |
| Release date | `property="datePublished"` |
| Cover image | `property="image"` |
| Screenshots | `property="screenshot"` |
| Description | `property="description"` |
| Genres | `property="genre"` |
| Platforms | `property="gamePlatform"` |

## 5. Offers And Shop Markup

The best available deal for the game was modelled as an `Offer`.

| DealHunter data | RDFa/schema.org markup |
| --- | --- |
| Availability/deal | `typeof="Offer"` |
| Price | `property="price"` |
| Currency | `property="priceCurrency"` with value `EUR` |
| Stock availability | `property="availability"` |
| Offer URL | `property="url"` |
| Shop/seller | `rel="seller"` and `typeof="Organization"` |
| Shop name | `property="name"` |

## 6. Reviews And Aggregate Rating

The review section follows the same structure as the restaurant tutorial.

Each review is marked as:

```html
typeof="Review"
```

Each review contains:

| DealHunter data | RDFa/schema.org markup |
| --- | --- |
| Review text | `property="reviewBody"` |
| Review rating | `rel="reviewRating"` and `typeof="Rating"` |
| Rating value | `property="ratingValue"` |
| Minimum rating | `property="worstRating"` |
| Maximum rating | `property="bestRating"` |
| Review author | `rel="author"` and `typeof="Person"` |
| Author name | `property="name"` |
| Review date | `property="datePublished"` |

The page also includes an `AggregateRating` based on all reviews for that game:

| DealHunter data | RDFa/schema.org markup |
| --- | --- |
| Average review score | `property="ratingValue"` |
| Number of reviews | `property="reviewCount"` |
| Minimum rating | `property="worstRating"` |
| Maximum rating | `property="bestRating"` |

## 7. Backend Support

The detail page needed two extra values to generate the aggregate rating:

- `average_rating`
- `review_count`

These are calculated in `GameDetailView` in `games/views.py` using Django aggregation.

This allows the template to generate real semantic data instead of hardcoded values.

## 8. Extra Improvement: Home Page Semantic Markup

Although the official requirement focuses on one detail page, we also added a lighter RDFa implementation to the home/catalog page as an extra improvement.

Each game card in the home grid is marked as:

```html
typeof="VideoGame Product"
```

Each card includes:

| Game card data | RDFa/schema.org markup |
| --- | --- |
| Detail page URL | `property="url"` |
| Cover image | `property="image"` |
| Game title | `property="name"` |
| Genres | `property="genre"` |
| Platform | `property="gamePlatform"` |
| Price/deal | `typeof="Offer"` |
| Price | `property="price"` |
| Currency | `property="priceCurrency"` |
| Availability | `property="availability"` |

This makes the list page semantically understandable too, not only the detail page.

## 9. Validation

The generated HTML was validated using the tools mentioned in the official tutorial:

- Google Rich Results Test / Structured Data Evaluation Tool
- RDFa Play

### 9.1 Detail Page Validation

Validated page:

- `/game/2/`
- Game: `ALL WILL FALL`

Detected structured data included:

- `VideoGame`
- `Product`
- `Offer`
- `Organization`
- `AggregateRating`
- `Review`
- `Rating`
- `Person`

Screenshot placeholders:

- `[Insert screenshot: Google summary for game detail page, 4 valid elements]`
- `[Insert screenshot: Google detail fields for reviews/aggregate rating]`
- `[Insert screenshot: RDFa Play graph for game detail page]`

### 9.2 Home Page Validation

Validated page:

- `/`

Detected structured data included multiple game cards with:

- `VideoGame`
- `Product`
- `Offer`
- `price`
- `priceCurrency`
- `genre`
- `gamePlatform`

Screenshot placeholders:

- `[Insert screenshot: Google summary for home page, 30/60 valid elements]`
- `[Insert screenshot: Google detail view for one home page game card]`
- `[Insert screenshot: RDFa Play graph for home page]`

## 10. Google Warnings

Google reported some optional warnings, such as:

- Missing `shippingDetails`
- Missing `hasMerchantReturnPolicy`
- Missing global product identifier such as GTIN or brand
- Missing review or aggregate rating in some home page product fragments

These are not critical errors. They are optional Google commerce fields and are outside the minimum scope of the RDFa activity. The structured data was still detected as valid.

## 11. Testing

The implementation was checked with:

```bash
dhunter/bin/python manage.py check
dhunter/bin/python manage.py test games
```

Both commands passed successfully.

The pages were also rendered locally to confirm that the generated HTML contains the expected RDFa markup.

## 12. Final Summary

The Web 3.0 delivery requirement was fulfilled by adding RDFa semantic markup to the game detail page using schema.org vocabulary.

The implementation follows the same pattern as the teacher's restaurant tutorial, but adapted to the DealHunter domain.

Additionally, a stronger solution was implemented by adding lighter RDFa markup to the home catalog page, allowing each game card to be understood semantically by search engines and RDFa parsers.

## 13. Possible Future Improvements

Possible improvements beyond the current delivery:

- Add richer semantic fields to the home page cards, such as descriptions when available.
- Add brand or identifier fields if stable external videogame identifiers are introduced.
- Add seller details to every home page offer.
- Improve ordering of availability data so the displayed card price always corresponds to the cheapest offer.
- Validate with `validator.schema.org` as an additional optional check.
